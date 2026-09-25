"""Tests for `atlas stats`."""

from __future__ import annotations

import json
from pathlib import Path

from founder_atlas_pipeline.stats import collect_stats, format_stats


def _touch(path: Path, text: str = "") -> None:
    path.write_text(text, encoding="utf-8")


def _advice(category: str) -> str:
    return f"---\nid: x\ncategory: {category}\n---\nbody\n"


def test_collect_stats_counts_files_and_advice_per_category(content_root: Path) -> None:
    _touch(content_root / "sources" / "a.md")
    _touch(content_root / "sources" / "a.transcript.json", "{}")
    _touch(content_root / "advice" / "a--01.md", _advice("pricing"))
    _touch(content_root / "advice" / "a--02.md", _advice("pricing"))
    _touch(content_root / "advice" / "a--03.md", _advice("team"))
    _touch(content_root / "keywords" / "pricing-strategy.md")

    stats = collect_stats(content_root)

    assert (stats.sources, stats.advice, stats.keyword_pages) == (1, 3, 1)
    assert stats.advice_per_category["pricing"] == 2
    assert stats.advice_per_category["team"] == 1
    assert stats.advice_per_category["idea"] == 0
    assert stats.over_cap_categories == []


def test_collect_stats_flags_category_over_twenty_keywords(content_root: Path) -> None:
    keywords = "\n".join(f"      - {{ slug: k{i}, title: K{i} }}" for i in range(21))
    (content_root / "taxonomy.yaml").write_text(
        f"categories:\n  - slug: idea\n    title: I\n    color: '#000'\n    keywords:\n{keywords}\n",
        encoding="utf-8",
    )

    stats = collect_stats(content_root)

    assert stats.over_cap_categories == ["idea"]
    assert stats.has_errors


def test_collect_stats_counts_unanswered_questions(content_root: Path) -> None:
    lines = [
        {"question": "q1", "matched": ["pricing-strategy"], "answered": True},
        {"question": "q2", "matched": [], "answered": False},
        {"question": "q3", "matched": [], "answered": False},
    ]
    (content_root / "questions" / "log.jsonl").write_text(
        "\n".join(json.dumps(line) for line in lines) + "\n", encoding="utf-8"
    )

    stats = collect_stats(content_root)

    assert (stats.questions, stats.unanswered_questions) == (3, 2)


def test_format_stats_mentions_key_numbers(content_root: Path) -> None:
    text = format_stats(collect_stats(content_root))

    assert "sources: 0" in text
    assert "unanswered questions: 0" in text
