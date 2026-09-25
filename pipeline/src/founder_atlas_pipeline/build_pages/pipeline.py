"""Orchestrates `atlas build-pages`: advice units -> content/keywords/{slug}.md.

Two rules from the task brief are enforced here, not left to the LLM:
- Evidence markers (`{{advice:id}}`) that reference an id the model wasn't
  given as material are stripped before writing.
- A page already marked `reviewed: true` is left untouched unless `--force`
  is passed; regenerating it resets `reviewed` back to `false`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from founder_atlas_pipeline.advice import list_all_advice
from founder_atlas_pipeline.build_pages.client import PageWriterClient
from founder_atlas_pipeline.keywords import keyword_exists, read_keyword, write_keyword
from founder_atlas_pipeline.models import AdviceUnit, KeywordImage, KeywordPage
from founder_atlas_pipeline.sources import read_source
from founder_atlas_pipeline.taxonomy import Taxonomy

_EVIDENCE_MARKER = re.compile(r"\{\{advice:([\w-]+)\}\}")


@dataclass(frozen=True)
class BuildPagesStats:
    """Summary of one `build_pages` run, for CLI logging."""

    written: list[str] = field(default_factory=list)
    preserved_reviewed: list[str] = field(default_factory=list)
    skipped_no_advice: int = 0


def _group_advice_by_keyword(advice_units: list[AdviceUnit]) -> dict[str, list[AdviceUnit]]:
    grouped: dict[str, list[AdviceUnit]] = {}
    for unit in advice_units:
        for keyword_slug in unit.keywords:
            grouped.setdefault(keyword_slug, []).append(unit)
    return grouped


def _filter_evidence_markers(body: str, valid_ids: set[str]) -> tuple[str, list[str]]:
    """Strip `{{advice:id}}` markers whose id isn't in `valid_ids`.

    Args:
        body: The page's raw Markdown body, as proposed by the model.
        valid_ids: Advice ids the model was actually given as material.

    Returns:
        The cleaned body, and the list of ids actually cited (in the order
        they first appear), which becomes the page's `advice` frontmatter.
    """
    used_ids: list[str] = []

    def _replace(match: re.Match[str]) -> str:
        advice_id = match.group(1)
        if advice_id not in valid_ids:
            return ""
        if advice_id not in used_ids:
            used_ids.append(advice_id)
        return match.group(0)

    cleaned = _EVIDENCE_MARKER.sub(_replace, body)
    cleaned = re.sub(r" {2,}", " ", cleaned)
    cleaned = re.sub(r" +\n", "\n", cleaned)
    return cleaned, used_ids


def _collect_images(
    content_root: Path, used_ids: list[str], advice_by_id: dict[str, AdviceUnit]
) -> list[KeywordImage]:
    """Pick one image per distinct cited source, preferring its thumbnail."""
    images: list[KeywordImage] = []
    seen_sources: set[str] = set()
    for advice_id in used_ids:
        source_id = advice_by_id[advice_id].source
        if source_id in seen_sources:
            continue
        seen_sources.add(source_id)
        source_meta = read_source(content_root, source_id)
        src = source_meta.thumbnail or (source_meta.images[0] if source_meta.images else None)
        if src is not None:
            images.append(KeywordImage(src=src, alt=source_meta.title_ko, source=source_id))
    return images


def build_pages(
    content_root: Path,
    taxonomy: Taxonomy,
    client: PageWriterClient,
    keyword_slug: str | None = None,
    force: bool = False,
    today: str | None = None,
) -> BuildPagesStats:
    """Build (or rebuild) keyword pages from the advice units that cite them.

    Args:
        content_root: The `content/` directory.
        taxonomy: The loaded taxonomy (source of keyword/category titles).
        client: The `PageWriterClient` to call per keyword.
        keyword_slug: If given, only build this one keyword's page.
        force: If True, regenerate pages even if already `reviewed: true`.
        today: ISO date string for `updated_at`. Defaults to today (UTC).

    Returns:
        `BuildPagesStats` describing what was written, preserved, or skipped.

    Raises:
        KeyError: If `keyword_slug` is given but isn't in `taxonomy`.
    """
    grouped = _group_advice_by_keyword(list_all_advice(content_root))
    updated_at = today or datetime.now(timezone.utc).date().isoformat()

    written: list[str] = []
    preserved_reviewed: list[str] = []
    skipped_no_advice = 0

    for category in taxonomy.categories:
        for keyword in category.keywords:
            if keyword_slug is not None and keyword.slug != keyword_slug:
                continue

            advice_units = grouped.get(keyword.slug, [])
            if not advice_units:
                skipped_no_advice += 1
                continue

            if keyword_exists(content_root, keyword.slug) and not force:
                existing = read_keyword(content_root, keyword.slug)
                if existing.reviewed:
                    preserved_reviewed.append(keyword.slug)
                    continue

            related_keywords = {
                other.slug: other.title for other in category.keywords if other.slug != keyword.slug
            }
            candidate = client.write_page(
                keyword_title=keyword.title,
                category_title=category.title,
                advice_units=advice_units,
                related_keywords=related_keywords,
            )

            advice_by_id = {unit.id: unit for unit in advice_units}
            body, used_ids = _filter_evidence_markers(candidate.body_ko, set(advice_by_id))
            images = _collect_images(content_root, used_ids, advice_by_id)

            page = KeywordPage(
                slug=keyword.slug,
                title=candidate.title,
                category=category.slug,
                summary=candidate.summary,
                reviewed=False,
                advice=used_ids,
                images=images,
                updated_at=updated_at,
                body_ko=body,
            )
            write_keyword(content_root, page)
            written.append(keyword.slug)

    if keyword_slug is not None and not written and not preserved_reviewed and skipped_no_advice == 0:
        raise KeyError(f"keyword slug '{keyword_slug}' not found in taxonomy")

    return BuildPagesStats(
        written=written, preserved_reviewed=preserved_reviewed, skipped_no_advice=skipped_no_advice
    )
