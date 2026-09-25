"""`atlas discover`: list real candidate URLs per origin into `pipeline/candidates/`.

URLs always come from a real listing (YouTube channel/search via yt-dlp,
paulgraham.com/articles.html, a16z's post sitemap) and are never invented.
a16z has no working RSS feed (/feed/ returns 404); robots.txt points to the
sitemap index and allows crawling.
`CandidateLister` is a Protocol so tests run without the network.
"""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Protocol

import defusedxml.ElementTree as ElementTree
import requests

from founder_atlas_pipeline.ingest.pipeline import ORIGINS, is_video_id

PAUL_GRAHAM_INDEX = "https://paulgraham.com/articles.html"
A16Z_SITEMAP = "https://a16z.com/post-sitemap.xml"
_SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
YOUTUBE_LISTINGS = {
    "yc-youtube": "https://www.youtube.com/@ycombinator/videos",
    "lightcone": "https://www.youtube.com/@ycombinator/search?query=lightcone",
}
_PG_NON_ESSAYS = {"index.html", "articles.html", "rss.html", "bio.html", "books.html"}
_HTTP_TIMEOUT_SECONDS = 30
_HEADERS = {"User-Agent": "founder-atlas-pipeline/0.1 (personal research tool)"}


class CandidateLister(Protocol):
    """Lists candidate source URLs for one origin."""

    def list_urls(self, origin: str, limit: int) -> list[str]:
        """Return up to `limit` URLs, newest/most-listed first."""
        ...


class _LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.hrefs.append(href)


def _unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def parse_paul_graham_articles(html: str) -> list[str]:
    """Extract essay URLs from paulgraham.com/articles.html.

    Args:
        html: The articles index page HTML.

    Returns:
        Absolute essay URLs in page order, without duplicates or non-essay pages.
    """
    collector = _LinkCollector()
    collector.feed(html)
    essays = [
        f"https://paulgraham.com/{href}"
        for href in collector.hrefs
        if "/" not in href and href.endswith(".html") and href not in _PG_NON_ESSAYS
    ]
    return _unique(essays)


def _text(element: Any, tag: str) -> str:
    return (element.findtext(f"{_SITEMAP_NS}{tag}") or "").strip()


def parse_sitemap_links(xml_text: str) -> list[str]:
    """Extract page URLs from a sitemap `urlset`, newest `lastmod` first.

    Args:
        xml_text: The sitemap XML.

    Returns:
        Unique URLs sorted by `lastmod` descending; undated URLs go last.
    """
    root = ElementTree.fromstring(xml_text)
    dated = [
        (_text(url, "lastmod"), _text(url, "loc")) for url in root.iter(f"{_SITEMAP_NS}url")
    ]
    ordered = sorted((pair for pair in dated if pair[1]), key=lambda pair: pair[0], reverse=True)
    return _unique([loc for _, loc in ordered])


def youtube_watch_urls(entries: list[dict[str, Any]]) -> list[str]:
    """Turn yt-dlp flat-playlist entries into watch URLs, keeping videos only.

    Search listings mix in playlists (ids like `PL...`); those are dropped.

    Args:
        entries: yt-dlp `entries` from a flat extraction.

    Returns:
        Watch URLs for entries whose id is an 11-character video id.
    """
    ids = [str(entry.get("id") or "") for entry in entries]
    return [f"https://www.youtube.com/watch?v={vid}" for vid in ids if is_video_id(vid)]


def append_candidates(path: Path, urls: list[str]) -> int:
    """Append URLs to a candidates file, skipping ones already present.

    Args:
        path: The candidates file (created with parent dirs if missing).
        urls: URLs to add.

    Returns:
        How many new URLs were written.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    new_urls = [url for url in _unique(urls) if url not in set(existing)]
    path.write_text("\n".join([*existing, *new_urls]) + "\n", encoding="utf-8")
    return len(new_urls)


def discover(origin: str, limit: int, *, candidates_dir: Path, lister: CandidateLister) -> int:
    """List candidates for one origin and append them to `{candidates_dir}/{origin}.txt`.

    Args:
        origin: One of the four supported origins.
        limit: Maximum number of URLs to list.
        candidates_dir: Directory holding per-origin candidate files.
        lister: The URL lister to use.

    Returns:
        How many new URLs were added.

    Raises:
        ValueError: If `origin` isn't supported.
    """
    if origin not in ORIGINS:
        raise ValueError(f"unknown origin '{origin}', expected one of {ORIGINS}")
    urls = lister.list_urls(origin, limit)[:limit]
    return append_candidates(candidates_dir / f"{origin}.txt", urls)


class WebCandidateLister:
    """Real `CandidateLister` backed by yt-dlp and plain HTTP."""

    def list_urls(self, origin: str, limit: int) -> list[str]:
        """List candidate URLs for `origin` from its real public listing.

        Args:
            origin: One of the four supported origins.
            limit: Maximum number of URLs to return.

        Returns:
            Up to `limit` URLs.
        """
        if origin in YOUTUBE_LISTINGS:
            return self._list_youtube(YOUTUBE_LISTINGS[origin], limit)
        if origin == "paul-graham":
            return parse_paul_graham_articles(self._get(PAUL_GRAHAM_INDEX))[:limit]
        return parse_sitemap_links(self._get(A16Z_SITEMAP))[:limit]

    @staticmethod
    def _get(url: str) -> str:
        response = requests.get(url, timeout=_HTTP_TIMEOUT_SECONDS, headers=_HEADERS)
        response.raise_for_status()
        return response.text

    @staticmethod
    def _list_youtube(listing_url: str, limit: int) -> list[str]:
        import yt_dlp

        options = {"quiet": True, "no_warnings": True, "extract_flat": True, "playlistend": limit}
        with yt_dlp.YoutubeDL(options) as ydl:
            info: dict[str, Any] = ydl.extract_info(listing_url, download=False)
        return youtube_watch_urls(list(info.get("entries") or []))[:limit]
