"""Tests for the extract pipeline: candidate -> verify -> write advice.

Uses a fake `ExtractClient` so no network/Claude API call happens in tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from founder_atlas_pipeline.advice import list_advice_ids, read_advice
from founder_atlas_pipeline.extract.client import ExtractionCandidate
from founder_atlas_pipeline.extract.pipeline import extract_source
from founder_atlas_pipeline.models import SourceMeta, Transcript, TranscriptSegment
from founder_atlas_pipeline.sources import write_source
from founder_atlas_pipeline.taxonomy import load_taxonomy


class FakeExtractClient:
    """Test double: returns a preset list of candidates per chunk, in order."""

    def __init__(self, candidates_per_chunk: list[list[ExtractionCandidate]]) -> None:
        self._candidates_per_chunk = candidates_per_chunk
        self.calls: list[str] = []

    def extract_candidates(
        self, chunk_text, *, source_title, speakers, category_slugs, keyword_slugs
    ):
        self.calls.append(chunk_text)
        return self._candidates_per_chunk[len(self.calls) - 1]


SEGMENTS = [
    TranscriptSegment(start=0.0, duration=5.0, text="Welcome back to the show today."),
    TranscriptSegment(start=5.0, duration=6.0, text="Charge more than you think you should."),
    TranscriptSegment(start=11.0, duration=4.0, text="That is the whole pricing lesson."),
]


def _seed_source(content_root: Path, source_id: str = "yc-youtube-pricing") -> None:
    meta = SourceMeta(
        id=source_id,
        title="Pricing 101",
        title_ko="가격 책정 101",
        url="https://www.youtube.com/watch?v=abc123",
        origin="yc-youtube",
        format="video",
        youtube_id="abc123",
        published="2024-03-01",
        speakers=["Kevin Hale"],
        thumbnail=None,
        images=[],
        ingested_at="2026-09-25",
        summary_ko="가격 책정에 대한 영상.",
    )
    write_source(content_root, meta, Transcript(kind="segments", segments=SEGMENTS))


def _valid_candidate(**overrides) -> ExtractionCandidate:
    defaults = dict(
        claim="초기에는 가격을 높게 시작하라",
        body_ko="가격을 낮게 시작하면 나중에 올리기 어렵습니다.",
        quote="Charge more than you think you should.",
        category="pricing",
        keywords=["pricing-strategy"],
        stage=["pre-seed"],
        domain=["b2b"],
        speaker="Kevin Hale",
    )
    defaults.update(overrides)
    return ExtractionCandidate(**defaults)


def test_valid_candidate_is_verified_and_written(content_root: Path) -> None:
    _seed_source(content_root)
    taxonomy = load_taxonomy(content_root / "taxonomy.yaml")
    client = FakeExtractClient([[_valid_candidate()]])

    stats = extract_source(content_root, "yc-youtube-pricing", taxonomy, client)

    assert stats.total_candidates == 1
    assert stats.written == 1
    assert stats.dropped_low_score == 0
    assert stats.dropped_invalid_taxonomy == 0
    assert stats.dropped_duplicate_quote == 0
    assert stats.written_ids == ["yc-youtube-pricing--01"]

    unit = read_advice(content_root, "yc-youtube-pricing--01")
    assert unit.claim == "초기에는 가격을 높게 시작하라"
    assert unit.anchor.kind == "timestamp"
    assert unit.anchor.start == 5
    assert unit.match_score >= 90


def test_quote_that_does_not_match_transcript_is_dropped(content_root: Path) -> None:
    _seed_source(content_root)
    taxonomy = load_taxonomy(content_root / "taxonomy.yaml")
    bad = _valid_candidate(quote="This sentence never appears anywhere in the transcript.")
    client = FakeExtractClient([[bad]])

    stats = extract_source(content_root, "yc-youtube-pricing", taxonomy, client)

    assert stats.written == 0
    assert stats.dropped_low_score == 1
    assert list_advice_ids(content_root) == []


@pytest.mark.parametrize(
    "overrides",
    [
        {"category": "not-a-real-category"},
        {"keywords": ["not-a-real-keyword"]},
        {"keywords": []},
        {"keywords": ["pricing-strategy", "unit-economics", "billing-model", "gross-margin"]},
        {"stage": ["not-a-real-stage"]},
        {"domain": ["not-a-real-domain"]},
    ],
)
def test_invalid_taxonomy_fields_are_dropped(content_root: Path, overrides: dict) -> None:
    _seed_source(content_root)
    taxonomy = load_taxonomy(content_root / "taxonomy.yaml")
    client = FakeExtractClient([[_valid_candidate(**overrides)]])

    stats = extract_source(content_root, "yc-youtube-pricing", taxonomy, client)

    assert stats.written == 0
    assert stats.dropped_invalid_taxonomy == 1


def test_extract_calls_client_once_per_chunk(content_root: Path) -> None:
    _seed_source(content_root)
    taxonomy = load_taxonomy(content_root / "taxonomy.yaml")
    client = FakeExtractClient([[], [], []])

    stats = extract_source(content_root, "yc-youtube-pricing", taxonomy, client, chunk_max_chars=30)

    assert len(client.calls) == 3
    assert stats.total_candidates == 0


def test_advice_ids_continue_from_existing_advice(content_root: Path) -> None:
    _seed_source(content_root)
    taxonomy = load_taxonomy(content_root / "taxonomy.yaml")

    # First extraction run writes --01.
    client1 = FakeExtractClient([[_valid_candidate()]])
    extract_source(content_root, "yc-youtube-pricing", taxonomy, client1)

    # A second run (e.g. re-extract) should continue at --02, not collide.
    client2 = FakeExtractClient([[_valid_candidate(
        claim="다른 조언", quote="That is the whole pricing lesson."
    )]])
    stats2 = extract_source(content_root, "yc-youtube-pricing", taxonomy, client2)

    assert stats2.written_ids == ["yc-youtube-pricing--02"]
    assert set(list_advice_ids(content_root)) == {
        "yc-youtube-pricing--01",
        "yc-youtube-pricing--02",
    }


def test_multiple_candidates_in_one_chunk_get_sequential_ids(content_root: Path) -> None:
    _seed_source(content_root)
    taxonomy = load_taxonomy(content_root / "taxonomy.yaml")
    client = FakeExtractClient(
        [[_valid_candidate(claim="첫 번째"), _valid_candidate(
            claim="두 번째", quote="That is the whole pricing lesson."
        )]]
    )

    stats = extract_source(content_root, "yc-youtube-pricing", taxonomy, client)

    assert stats.written_ids == ["yc-youtube-pricing--01", "yc-youtube-pricing--02"]


def test_duplicate_quote_from_overlapping_chunks_is_written_once(content_root: Path) -> None:
    _seed_source(content_root)
    taxonomy = load_taxonomy(content_root / "taxonomy.yaml")
    client = FakeExtractClient([[
        _valid_candidate(),
        _valid_candidate(claim="같은 인용을 다시 해석", quote="  CHARGE more than you think you should. "),
    ]])

    stats = extract_source(content_root, "yc-youtube-pricing", taxonomy, client)

    assert stats.written == 1
    assert stats.dropped_duplicate_quote == 1
    assert stats.written_ids == ["yc-youtube-pricing--01"]


def test_reextract_skips_quote_already_written(content_root: Path) -> None:
    _seed_source(content_root)
    taxonomy = load_taxonomy(content_root / "taxonomy.yaml")
    extract_source(content_root, "yc-youtube-pricing", taxonomy, FakeExtractClient([[_valid_candidate()]]))

    stats = extract_source(
        content_root,
        "yc-youtube-pricing",
        taxonomy,
        FakeExtractClient([[_valid_candidate(claim="중복 재추출")]]),
    )

    assert stats.written == 0
    assert stats.dropped_duplicate_quote == 1
    assert list_advice_ids(content_root, "yc-youtube-pricing") == ["yc-youtube-pricing--01"]
