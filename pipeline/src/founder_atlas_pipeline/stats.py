"""`atlas stats`: counts across `content/` plus the 20-keywords-per-category cap check.

Reads `taxonomy.yaml` raw (not via `load_taxonomy`) so an over-cap taxonomy is
reported instead of aborting the whole command.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from founder_atlas_pipeline.frontmatter import parse

MAX_KEYWORDS_PER_CATEGORY = 20


@dataclass(frozen=True)
class ContentStats:
    """Snapshot of what's in `content/`."""

    sources: int
    advice: int
    keyword_pages: int
    advice_per_category: dict[str, int] = field(default_factory=dict)
    over_cap_categories: list[str] = field(default_factory=list)
    questions: int = 0
    unanswered_questions: int = 0

    @property
    def has_errors(self) -> bool:
        """True when the taxonomy breaks the 20-keywords-per-category rule."""
        return bool(self.over_cap_categories)


def _read_categories(content_root: Path) -> list[dict]:
    raw = yaml.safe_load((content_root / "taxonomy.yaml").read_text(encoding="utf-8")) or {}
    return list(raw.get("categories") or [])


def _advice_categories(content_root: Path) -> list[str]:
    return [
        str(parse(path.read_text(encoding="utf-8")).frontmatter.get("category", ""))
        for path in sorted((content_root / "advice").glob("*.md"))
    ]


def _read_questions(content_root: Path) -> list[dict]:
    log = content_root / "questions" / "log.jsonl"
    if not log.exists():
        return []
    lines = log.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def collect_stats(content_root: Path) -> ContentStats:
    """Count sources, advice, keyword pages, and questions under `content/`.

    Args:
        content_root: The `content/` directory.

    Returns:
        A `ContentStats` snapshot.
    """
    categories = _read_categories(content_root)
    advice_categories = _advice_categories(content_root)
    questions = _read_questions(content_root)
    return ContentStats(
        sources=len(list((content_root / "sources").glob("*.md"))),
        advice=len(advice_categories),
        keyword_pages=len(list((content_root / "keywords").glob("*.md"))),
        advice_per_category={
            c["slug"]: advice_categories.count(c["slug"]) for c in categories
        },
        over_cap_categories=[
            c["slug"]
            for c in categories
            if len(c.get("keywords") or []) > MAX_KEYWORDS_PER_CATEGORY
        ],
        questions=len(questions),
        unanswered_questions=sum(1 for q in questions if not q.get("answered")),
    )


def format_stats(stats: ContentStats) -> str:
    """Render stats as plain text for the CLI.

    Args:
        stats: The snapshot to render.

    Returns:
        Multi-line human-readable text.
    """
    lines = [
        f"sources: {stats.sources}",
        f"advice: {stats.advice}",
        f"keyword pages: {stats.keyword_pages}",
        "advice per category:",
        *(f"  {slug}: {count}" for slug, count in stats.advice_per_category.items()),
        f"questions: {stats.questions}",
        f"unanswered questions: {stats.unanswered_questions}",
    ]
    if stats.over_cap_categories:
        lines.append(
            f"ERROR: over {MAX_KEYWORDS_PER_CATEGORY} keywords in: "
            f"{', '.join(stats.over_cap_categories)}"
        )
    return "\n".join(lines)
