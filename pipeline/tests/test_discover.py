"""Tests for `atlas discover`: listing real candidate URLs per origin."""

from __future__ import annotations

from pathlib import Path

import pytest

from founder_atlas_pipeline.discover import (
    append_candidates,
    discover,
    parse_paul_graham_articles,
    parse_sitemap_links,
    youtube_watch_urls,
)

PG_HTML = """
<html><body><table><tr><td>
<a href="index.html"><img src="x.gif"></a>
<font><a href="greatwork.html">How to Do Great Work</a><br>
<a href="ds.html">Do Things that Don't Scale</a><br>
<a href="https://twitter.com/paulg">Twitter</a>
<a href="rss.html">RSS</a>
<a href="ds.html">Do Things that Don't Scale</a>
</font></td></tr></table></body></html>
"""

SITEMAP_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://a16z.com/old-post/</loc><lastmod>2021-01-01T00:00:00+00:00</lastmod></url>
  <url><loc> https://a16z.com/new-post/ </loc><lastmod>2026-09-01T00:00:00+00:00</lastmod></url>
  <url><loc>https://a16z.com/no-date/</loc></url>
</urlset>
"""


def test_parse_paul_graham_articles_keeps_essays_only_in_order() -> None:
    urls = parse_paul_graham_articles(PG_HTML)

    assert urls == ["https://paulgraham.com/greatwork.html", "https://paulgraham.com/ds.html"]


def test_parse_sitemap_links_sorts_newest_first_and_strips_whitespace() -> None:
    assert parse_sitemap_links(SITEMAP_XML) == [
        "https://a16z.com/new-post/",
        "https://a16z.com/old-post/",
        "https://a16z.com/no-date/",
    ]


def test_youtube_watch_urls_drops_playlist_entries() -> None:
    entries = [{"id": "PLQ-uHSnFig5Ob4XXhgSK26Smb4oRhzFmK"}, {"id": "8OOuCnZB-4o"}, {}]

    assert youtube_watch_urls(entries) == ["https://www.youtube.com/watch?v=8OOuCnZB-4o"]


def test_append_candidates_dedupes_against_existing_file(tmp_path: Path) -> None:
    path = tmp_path / "candidates" / "a16z.txt"

    first = append_candidates(path, ["u1", "u2"])
    second = append_candidates(path, ["u2", "u3", "u3"])

    assert (first, second) == (2, 1)
    assert path.read_text(encoding="utf-8").splitlines() == ["u1", "u2", "u3"]


class FakeLister:
    def list_urls(self, origin: str, limit: int) -> list[str]:
        return [f"https://example/{origin}/{i}" for i in range(limit)]


def test_discover_writes_to_origin_file_and_respects_limit(tmp_path: Path) -> None:
    added = discover("lightcone", 3, candidates_dir=tmp_path, lister=FakeLister())

    lines = (tmp_path / "lightcone.txt").read_text(encoding="utf-8").splitlines()
    assert added == 3
    assert lines == [f"https://example/lightcone/{i}" for i in range(3)]


def test_discover_rejects_unknown_origin(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        discover("sequoia", 3, candidates_dir=tmp_path, lister=FakeLister())
