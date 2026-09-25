"""Orchestrates `atlas ingest`: URL -> content/sources/{id}.md + .transcript.json.

`title_ko` and the Korean summary body are left empty at ingest time: ingest
is network-only (no API key needed) so the 100-source collection can run
before a Claude key exists. The web app falls back to the original title.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from founder_atlas_pipeline.ingest.fetchers import FetchError, WebFetcher, YouTubeFetcher
from founder_atlas_pipeline.models import SourceMeta, Transcript
from founder_atlas_pipeline.slugs import make_source_id
from founder_atlas_pipeline.sources import source_exists, write_source

ORIGINS = ("yc-youtube", "lightcone", "paul-graham", "a16z")
_YOUTUBE_ORIGINS = {"yc-youtube", "lightcone"}
_YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}
_VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
_TEXT_ORIGIN_BY_HOST = {"paulgraham.com": "paul-graham", "a16z.com": "a16z"}
_FORMAT_BY_TEXT_ORIGIN = {"paul-graham": "essay", "a16z": "blog"}
_SITE_NAME_SUFFIX = re.compile(
    r"\s+[|\-–]\s+(andreessen horowitz|a16z|paul graham)\s*$", re.IGNORECASE
)


class IngestError(Exception):
    """Base class for per-URL ingest failures that shouldn't stop a batch."""


class UnsupportedSourceError(IngestError):
    """Raised when a URL doesn't belong to one of the four supported origins."""


@dataclass(frozen=True)
class IngestOutcome:
    """Result of ingesting one URL."""

    url: str
    status: str  # "written" | "skipped" | "failed"
    source_id: str | None = None
    error: str | None = None


def _host(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    return host.removeprefix("www.") if host not in _YOUTUBE_HOSTS else host


def is_video_id(candidate: str) -> bool:
    """Return True if `candidate` looks like an 11-character YouTube video id."""
    return bool(_VIDEO_ID.match(candidate))


def parse_youtube_id(url: str) -> str | None:
    """Extract the video id from a YouTube watch/short URL.

    Args:
        url: Any URL.

    Returns:
        The 11-character video id, or None if `url` isn't a YouTube video URL.
    """
    parsed = urlparse(url)
    if (parsed.hostname or "").lower() not in _YOUTUBE_HOSTS:
        return None
    if parsed.hostname == "youtu.be":
        candidate = parsed.path.lstrip("/")
    else:
        candidate = parse_qs(parsed.query).get("v", [""])[0]
    return candidate if is_video_id(candidate) else None


def infer_origin(url: str, override: str | None) -> str:
    """Decide which of the four origins a URL belongs to.

    YouTube can't tell YC from Lightcone by URL, so `override` decides
    (default `yc-youtube`). Text origins are decided by host.

    Args:
        url: The source URL.
        override: Explicit origin for YouTube URLs (`--origin`).

    Returns:
        One of `ORIGINS`.

    Raises:
        UnsupportedSourceError: If the host isn't supported or the override is
            inconsistent with the host.
    """
    if parse_youtube_id(url) is not None:
        origin = override or "yc-youtube"
        if origin not in _YOUTUBE_ORIGINS:
            raise UnsupportedSourceError(f"origin '{origin}' is not a YouTube origin: {url}")
        return origin
    origin = _TEXT_ORIGIN_BY_HOST.get(_host(url))
    if origin is None:
        raise UnsupportedSourceError(f"unsupported source host: {url}")
    return origin


def clean_title(title: str) -> str:
    """Drop a trailing site name like " | Andreessen Horowitz" from a page title.

    Args:
        title: The raw page title.

    Returns:
        The title without a known site-name suffix.
    """
    return _SITE_NAME_SUFFIX.sub("", title).strip()


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _fetch_video(
    url: str, origin: str, youtube: YouTubeFetcher, today: str
) -> tuple[SourceMeta, Transcript]:
    video_id = parse_youtube_id(url)
    if video_id is None:
        raise UnsupportedSourceError(f"not a YouTube video URL: {url}")
    metadata = youtube.fetch_metadata(video_id)
    segments = youtube.fetch_segments(video_id)
    meta = SourceMeta(
        id=make_source_id(origin, metadata.title),
        title=metadata.title,
        title_ko="",
        url=url,
        origin=origin,
        format="video",
        youtube_id=video_id,
        published=metadata.published,
        speakers=[],
        thumbnail=metadata.thumbnail,
        images=[],
        ingested_at=today,
        summary_ko="",
    )
    return meta, Transcript(kind="segments", segments=segments)


def _fetch_text(
    url: str, origin: str, web: WebFetcher, today: str
) -> tuple[SourceMeta, Transcript]:
    article = web.fetch_article(url)
    title = clean_title(article.title)
    meta = SourceMeta(
        id=make_source_id(origin, title),
        title=title,
        title_ko="",
        url=url,
        origin=origin,
        format=_FORMAT_BY_TEXT_ORIGIN[origin],
        published=article.published,
        speakers=["Paul Graham"] if origin == "paul-graham" else [],
        thumbnail=article.images[0] if article.images else None,
        images=list(article.images),
        ingested_at=today,
        summary_ko="",
    )
    return meta, Transcript(kind="paragraphs", paragraphs=list(article.paragraphs))


def ingest_url(
    content_root: Path,
    url: str,
    *,
    youtube: YouTubeFetcher,
    web: WebFetcher,
    origin: str | None = None,
    force: bool = False,
    today: str | None = None,
) -> IngestOutcome:
    """Fetch one URL and write its source metadata + transcript.

    Args:
        content_root: The `content/` directory.
        url: The source URL.
        youtube: Fetcher for YouTube URLs.
        web: Fetcher for essay/blog URLs.
        origin: Explicit origin override (needed to mark YouTube as lightcone).
        force: Overwrite an already-ingested source.
        today: ISO date for `ingested_at`. Defaults to today (UTC).

    Returns:
        An `IngestOutcome` with status `written` or `skipped`.

    Raises:
        UnsupportedSourceError: If the URL's origin is unsupported.
        FetchError: If metadata or text can't be fetched.
    """
    resolved_origin = infer_origin(url, origin)
    date = today or _today()
    if resolved_origin in _YOUTUBE_ORIGINS:
        meta, transcript = _fetch_video(url, resolved_origin, youtube, date)
    else:
        meta, transcript = _fetch_text(url, resolved_origin, web, date)
    if source_exists(content_root, meta.id) and not force:
        return IngestOutcome(url=url, status="skipped", source_id=meta.id)
    write_source(content_root, meta, transcript)
    return IngestOutcome(url=url, status="written", source_id=meta.id)


def ingest_many(
    content_root: Path,
    urls: list[str],
    *,
    youtube: YouTubeFetcher,
    web: WebFetcher,
    origin: str | None = None,
    force: bool = False,
) -> list[IngestOutcome]:
    """Ingest a batch of URLs, recording per-URL failures instead of raising.

    Args:
        content_root: The `content/` directory.
        urls: Source URLs, processed in order.
        youtube: Fetcher for YouTube URLs.
        web: Fetcher for essay/blog URLs.
        origin: Explicit origin override applied to every YouTube URL.
        force: Overwrite already-ingested sources.

    Returns:
        One `IngestOutcome` per URL, in input order.
    """
    outcomes: list[IngestOutcome] = []
    for url in urls:
        try:
            outcome = ingest_url(
                content_root, url, youtube=youtube, web=web, origin=origin, force=force
            )
        except (IngestError, FetchError) as error:
            outcome = IngestOutcome(url=url, status="failed", error=str(error))
        outcomes.append(outcome)
    return outcomes
