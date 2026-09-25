"""Tests for the build-pages pipeline.

Uses a fake `PageWriterClient` so no network/Claude API call happens in tests.
Covers the two rules called out in the task brief: evidence-id filtering
(a page can't cite an advice id it wasn't given) and reviewed-page
preservation (a human-approved page survives a rebuild unless --force).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from founder_atlas_pipeline.advice import write_advice
from founder_atlas_pipeline.build_pages.client import CLIPageWriterClient, PageCandidate
from founder_atlas_pipeline.build_pages.pipeline import build_pages
from founder_atlas_pipeline.keywords import keyword_path, read_keyword, write_keyword
from founder_atlas_pipeline.models import (
    AdviceAnchor,
    AdviceContext,
    AdviceUnit,
    KeywordImage,
    KeywordPage,
)
from founder_atlas_pipeline.sources import write_source
from founder_atlas_pipeline.taxonomy import load_taxonomy
from founder_atlas_pipeline.models import SourceMeta, Transcript


class FakePageWriterClient:
    """Test double: returns a preset `PageCandidate` per call, keyed by keyword title."""

    def __init__(self, pages: dict[str, PageCandidate]) -> None:
        self._pages = pages
        self.calls: list[str] = []

    def write_page(self, *, keyword_title, category_title, advice_units, related_keywords):
        self.calls.append(keyword_title)
        return self._pages[keyword_title]


def _source(content_root: Path, source_id: str) -> None:
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
        thumbnail="https://i.ytimg.com/vi/abc123/hqdefault.jpg",
        images=[],
        ingested_at="2026-09-25",
        summary_ko="가격 책정에 대한 영상.",
    )
    write_source(content_root, meta, Transcript(kind="segments", segments=[]))


def _advice(source_id: str, index: int, keyword: str, category: str = "pricing") -> AdviceUnit:
    return AdviceUnit(
        id=f"{source_id}--{index:02d}",
        source=source_id,
        category=category,
        keywords=[keyword],
        context=AdviceContext(stage=[], domain=[]),
        speaker="Kevin Hale",
        claim=f"조언 {index}",
        quote=f"quote {index}",
        anchor=AdviceAnchor(kind="timestamp", start=index * 10),
        match_score=95.0,
        body_ko=f"본문 {index}",
    )


def test_builds_page_for_keyword_with_advice(content_root: Path) -> None:
    _source(content_root, "src-a")
    write_advice(content_root, _advice("src-a", 1, "pricing-strategy"))
    taxonomy = load_taxonomy(content_root / "taxonomy.yaml")

    client = FakePageWriterClient(
        {
            "가격 책정": PageCandidate(
                title="가격 책정",
                summary="가격을 정하는 법",
                body_ko="본문입니다. {{advice:src-a--01}}",
            )
        }
    )

    stats = build_pages(content_root, taxonomy, client)

    assert stats.written == ["pricing-strategy"]
    page = read_keyword(content_root, "pricing-strategy")
    assert page.reviewed is False
    assert page.advice == ["src-a--01"]
    assert "{{advice:src-a--01}}" in page.body_ko
    assert page.images and page.images[0].source == "src-a"


def test_keyword_without_advice_is_skipped(content_root: Path) -> None:
    taxonomy = load_taxonomy(content_root / "taxonomy.yaml")
    client = FakePageWriterClient({})

    stats = build_pages(content_root, taxonomy, client)

    assert stats.written == []
    assert stats.skipped_no_advice > 0
    assert client.calls == []


def test_evidence_markers_for_unknown_ids_are_stripped(content_root: Path) -> None:
    _source(content_root, "src-a")
    write_advice(content_root, _advice("src-a", 1, "pricing-strategy"))
    taxonomy = load_taxonomy(content_root / "taxonomy.yaml")

    client = FakePageWriterClient(
        {
            "가격 책정": PageCandidate(
                title="가격 책정",
                summary="가격을 정하는 법",
                body_ko="본문. {{advice:src-a--01}} 그리고 {{advice:does-not-exist--99}}",
            )
        }
    )

    build_pages(content_root, taxonomy, client)

    page = read_keyword(content_root, "pricing-strategy")
    assert "{{advice:src-a--01}}" in page.body_ko
    assert "does-not-exist" not in page.body_ko
    assert page.advice == ["src-a--01"]


def test_reviewed_page_is_preserved_by_default(content_root: Path) -> None:
    _source(content_root, "src-a")
    write_advice(content_root, _advice("src-a", 1, "pricing-strategy"))
    taxonomy = load_taxonomy(content_root / "taxonomy.yaml")

    existing = KeywordPage(
        slug="pricing-strategy",
        title="가격 책정 (검수됨)",
        category="pricing",
        summary="사람이 이미 검수한 페이지",
        reviewed=True,
        advice=["src-a--01"],
        images=[],
        updated_at="2026-01-01",
        body_ko="검수된 본문.",
    )
    write_keyword(content_root, existing)

    client = FakePageWriterClient(
        {"가격 책정": PageCandidate(title="새 제목", summary="새 요약", body_ko="새 본문")}
    )

    stats = build_pages(content_root, taxonomy, client)

    assert stats.preserved_reviewed == ["pricing-strategy"]
    assert client.calls == []
    page = read_keyword(content_root, "pricing-strategy")
    assert page.title == "가격 책정 (검수됨)"
    assert page.reviewed is True


def test_force_overwrites_reviewed_page_and_resets_reviewed_flag(content_root: Path) -> None:
    _source(content_root, "src-a")
    write_advice(content_root, _advice("src-a", 1, "pricing-strategy"))
    taxonomy = load_taxonomy(content_root / "taxonomy.yaml")

    existing = KeywordPage(
        slug="pricing-strategy",
        title="가격 책정 (검수됨)",
        category="pricing",
        summary="사람이 이미 검수한 페이지",
        reviewed=True,
        advice=["src-a--01"],
        images=[],
        updated_at="2026-01-01",
        body_ko="검수된 본문.",
    )
    write_keyword(content_root, existing)

    client = FakePageWriterClient(
        {
            "가격 책정": PageCandidate(
                title="새 제목", summary="새 요약", body_ko="새 본문 {{advice:src-a--01}}"
            )
        }
    )

    stats = build_pages(content_root, taxonomy, client, force=True)

    assert stats.written == ["pricing-strategy"]
    page = read_keyword(content_root, "pricing-strategy")
    assert page.title == "새 제목"
    assert page.reviewed is False


def test_keyword_filter_only_builds_that_keyword(content_root: Path) -> None:
    _source(content_root, "src-a")
    write_advice(content_root, _advice("src-a", 1, "pricing-strategy"))
    write_advice(content_root, _advice("src-a", 2, "unit-economics"))
    taxonomy = load_taxonomy(content_root / "taxonomy.yaml")

    client = FakePageWriterClient(
        {
            "가격 책정": PageCandidate(title="t", summary="s", body_ko="b"),
            "Unit economics": PageCandidate(title="t2", summary="s2", body_ko="b2"),
        }
    )

    stats = build_pages(content_root, taxonomy, client, keyword_slug="pricing-strategy")

    assert stats.written == ["pricing-strategy"]
    assert client.calls == ["가격 책정"]


def test_images_deduplicated_by_source(content_root: Path) -> None:
    _source(content_root, "src-a")
    write_advice(content_root, _advice("src-a", 1, "pricing-strategy"))
    write_advice(content_root, _advice("src-a", 2, "pricing-strategy"))
    taxonomy = load_taxonomy(content_root / "taxonomy.yaml")

    client = FakePageWriterClient(
        {
            "가격 책정": PageCandidate(
                title="t", summary="s", body_ko="{{advice:src-a--01}} {{advice:src-a--02}}"
            )
        }
    )

    build_pages(content_root, taxonomy, client)

    page = read_keyword(content_root, "pricing-strategy")
    assert len(page.images) == 1


@pytest.mark.parametrize("provider", ["codex-cli", "claude-code-cli"])
def test_cli_page_writer_uses_only_public_advice_material(
    provider: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    import founder_atlas_pipeline.cli_providers as cli_providers

    calls = []

    def fake_run(selected, *, system_prompt, user_prompt, schema):
        calls.append((selected, system_prompt, user_prompt, schema))
        return {"title": "가격 책정", "summary": "한 줄 요약", "body_ko": "본문 {{advice:src-a--01}}"}

    monkeypatch.setattr(cli_providers, "run_structured_cli", fake_run)
    result = CLIPageWriterClient(provider).write_page(
        keyword_title="가격 책정",
        category_title="가격",
        advice_units=[_advice("src-a", 1, "pricing-strategy")],
        related_keywords={"unit-economics": "단위 경제"},
    )

    assert result.body_ko == "본문 {{advice:src-a--01}}"
    selected, system_prompt, user_prompt, schema = calls[0]
    assert selected == provider
    assert "src-a--01" in user_prompt
    assert "quote 1" not in user_prompt
    assert "unit-economics" in user_prompt
    assert schema["required"] == ["title", "summary", "body_ko"]
