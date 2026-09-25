"""Orchestrates `atlas extract`: chunk -> LLM candidates -> verify -> write advice.

Only advice with a code-computed `match_score >= MIN_MATCH_SCORE` is written
to `content/advice/` (per `CLAUDE.md`). Candidates with a category/keyword
outside `taxonomy.yaml`, or an out-of-range context attribute, are dropped
before verification even runs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from founder_atlas_pipeline.advice import list_advice_ids, write_advice
from founder_atlas_pipeline.chunking import DEFAULT_MAX_CHARS, chunk_transcript
from founder_atlas_pipeline.extract.client import ExtractClient, ExtractionCandidate
from founder_atlas_pipeline.models import AdviceAnchor, AdviceContext, AdviceUnit
from founder_atlas_pipeline.slugs import make_advice_id, next_advice_index
from founder_atlas_pipeline.sources import read_source, read_transcript
from founder_atlas_pipeline.taxonomy import VALID_DOMAINS, VALID_STAGES, Taxonomy
from founder_atlas_pipeline.verify import verify_quote_against_transcript

MIN_MATCH_SCORE = 90.0
MIN_KEYWORDS = 1
MAX_KEYWORDS = 3


@dataclass(frozen=True)
class ExtractStats:
    """Summary of one `extract_source` run, for CLI logging and `atlas stats`."""

    source_id: str
    total_candidates: int
    written: int
    dropped_low_score: int
    dropped_invalid_taxonomy: int
    written_ids: list[str] = field(default_factory=list)


def _taxonomy_reason(candidate: ExtractionCandidate, taxonomy: Taxonomy) -> str | None:
    """Return why `candidate` fails taxonomy validation, or `None` if it's valid."""
    if candidate.category not in taxonomy.category_slugs():
        return f"unknown category '{candidate.category}'"
    if not (MIN_KEYWORDS <= len(candidate.keywords) <= MAX_KEYWORDS):
        return f"keywords count {len(candidate.keywords)} not in [{MIN_KEYWORDS}, {MAX_KEYWORDS}]"
    unknown_keywords = set(candidate.keywords) - taxonomy.keyword_slugs()
    if unknown_keywords:
        return f"unknown keywords {sorted(unknown_keywords)}"
    if not set(candidate.stage) <= VALID_STAGES:
        return f"unknown stage(s) {sorted(set(candidate.stage) - VALID_STAGES)}"
    if not set(candidate.domain) <= VALID_DOMAINS:
        return f"unknown domain(s) {sorted(set(candidate.domain) - VALID_DOMAINS)}"
    return None


def extract_source(
    content_root: Path,
    source_id: str,
    taxonomy: Taxonomy,
    client: ExtractClient,
    chunk_max_chars: int = DEFAULT_MAX_CHARS,
) -> ExtractStats:
    """Extract, verify, and write advice units for one source.

    Args:
        content_root: The `content/` directory.
        source_id: The source id to extract from (must already be ingested).
        taxonomy: The loaded, validated taxonomy (for category/keyword checks).
        client: The `ExtractClient` to call per transcript chunk.
        chunk_max_chars: Soft per-chunk character budget (see `chunking.py`).

    Returns:
        `ExtractStats` describing how many candidates were proposed, written,
        and dropped (and why).
    """
    meta = read_source(content_root, source_id)
    transcript = read_transcript(content_root, source_id)
    chunks = chunk_transcript(transcript, max_chars=chunk_max_chars)

    category_slugs = sorted(taxonomy.category_slugs())
    keyword_slugs = sorted(taxonomy.keyword_slugs())

    candidates: list[ExtractionCandidate] = []
    for chunk in chunks:
        candidates.extend(
            client.extract_candidates(
                chunk.text,
                source_title=meta.title,
                speakers=meta.speakers,
                category_slugs=category_slugs,
                keyword_slugs=keyword_slugs,
            )
        )

    known_ids = list(list_advice_ids(content_root, source_id))
    written_ids: list[str] = []
    dropped_low_score = 0
    dropped_invalid_taxonomy = 0

    for candidate in candidates:
        if _taxonomy_reason(candidate, taxonomy) is not None:
            dropped_invalid_taxonomy += 1
            continue

        match = verify_quote_against_transcript(candidate.quote, transcript)
        if match.score < MIN_MATCH_SCORE:
            dropped_low_score += 1
            continue

        advice_id = make_advice_id(source_id, next_advice_index(known_ids + written_ids))
        unit = _build_advice_unit(advice_id, source_id, candidate, match.anchor, match.score)
        write_advice(content_root, unit)
        written_ids.append(advice_id)

    return ExtractStats(
        source_id=source_id,
        total_candidates=len(candidates),
        written=len(written_ids),
        dropped_low_score=dropped_low_score,
        dropped_invalid_taxonomy=dropped_invalid_taxonomy,
        written_ids=written_ids,
    )


def _build_advice_unit(
    advice_id: str,
    source_id: str,
    candidate: ExtractionCandidate,
    anchor: AdviceAnchor,
    score: float,
) -> AdviceUnit:
    return AdviceUnit(
        id=advice_id,
        source=source_id,
        category=candidate.category,
        keywords=list(candidate.keywords),
        context=AdviceContext(stage=list(candidate.stage), domain=list(candidate.domain)),
        speaker=candidate.speaker,
        claim=candidate.claim,
        quote=candidate.quote,
        anchor=anchor,
        match_score=round(score, 1),
        body_ko=candidate.body_ko,
    )
