"""Network fetchers for `atlas ingest`.

`YouTubeFetcher` / `WebFetcher` are Protocols so the ingest pipeline can be
tested with fakes. The real implementations wrap yt-dlp,
youtube-transcript-api, and trafilatura; their imports are local so the
module stays importable (and tests stay fast) without touching those libs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from founder_atlas_pipeline.models import TranscriptSegment

_MIN_PARAGRAPH_CHARS = 40


class FetchError(Exception):
    """Raised when a source's metadata or raw text can't be fetched."""


@dataclass(frozen=True)
class VideoMetadata:
    """Metadata for one YouTube video."""

    youtube_id: str
    title: str
    published: str | None
    thumbnail: str | None


@dataclass(frozen=True)
class Article:
    """Extracted main text and metadata for one essay/blog post."""

    title: str
    published: str | None
    paragraphs: list[str]
    images: list[str] = field(default_factory=list)


class YouTubeFetcher(Protocol):
    """Fetches YouTube metadata and English caption segments."""

    def fetch_metadata(self, video_id: str) -> VideoMetadata:
        """Return title/date/thumbnail for a video."""
        ...

    def fetch_segments(self, video_id: str) -> list[TranscriptSegment]:
        """Return English caption segments for a video."""
        ...


class WebFetcher(Protocol):
    """Fetches the main text of an essay or blog post."""

    def fetch_article(self, url: str) -> Article:
        """Return the article's title, date, paragraphs, and images."""
        ...


def _format_upload_date(raw: str | None) -> str | None:
    """Convert yt-dlp's `YYYYMMDD` into ISO `YYYY-MM-DD`."""
    if not raw or len(raw) != 8 or not raw.isdigit():
        return None
    return f"{raw[:4]}-{raw[4:6]}-{raw[6:]}"


class YtDlpYouTubeFetcher:
    """Real `YouTubeFetcher` using yt-dlp (metadata) + youtube-transcript-api (captions)."""

    def fetch_metadata(self, video_id: str) -> VideoMetadata:
        """Fetch video metadata with yt-dlp without downloading media.

        Args:
            video_id: The 11-character YouTube video id.

        Returns:
            The video's metadata.

        Raises:
            FetchError: If yt-dlp can't read the video.
        """
        import yt_dlp

        options = {"quiet": True, "no_warnings": True, "skip_download": True}
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                info: dict[str, Any] = ydl.extract_info(
                    f"https://www.youtube.com/watch?v={video_id}", download=False
                )
        except yt_dlp.utils.DownloadError as error:
            raise FetchError(f"yt-dlp could not read {video_id}: {error}") from error
        return VideoMetadata(
            youtube_id=video_id,
            title=str(info.get("title") or video_id),
            published=_format_upload_date(info.get("upload_date")),
            thumbnail=f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
        )

    def fetch_segments(self, video_id: str) -> list[TranscriptSegment]:
        """Fetch English caption segments (manual or auto-generated).

        Args:
            video_id: The 11-character YouTube video id.

        Returns:
            Caption segments in playback order.

        Raises:
            FetchError: If no English transcript is available.
        """
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api._errors import CouldNotRetrieveTranscript

        try:
            fetched = YouTubeTranscriptApi().fetch(video_id, languages=["en", "en-US"])
        except CouldNotRetrieveTranscript as error:
            raise FetchError(f"no English transcript for {video_id}: {error}") from error
        return [
            TranscriptSegment(start=float(s.start), duration=float(s.duration), text=s.text)
            for s in fetched
        ]


class TrafilaturaWebFetcher:
    """Real `WebFetcher` using trafilatura for main-text extraction."""

    def fetch_article(self, url: str) -> Article:
        """Download a page and extract its main text as paragraphs.

        Args:
            url: The essay/blog URL.

        Returns:
            The extracted article.

        Raises:
            FetchError: If the page can't be downloaded or has no main text.
        """
        import trafilatura

        html = trafilatura.fetch_url(url)
        if not html:
            raise FetchError(f"could not download {url}")
        text = trafilatura.extract(html, include_comments=False, include_tables=False)
        if not text:
            raise FetchError(f"no main text found at {url}")
        metadata = trafilatura.extract_metadata(html)
        image = getattr(metadata, "image", None) if metadata else None
        return Article(
            title=str(getattr(metadata, "title", None) or url),
            published=getattr(metadata, "date", None) if metadata else None,
            paragraphs=split_paragraphs(text),
            images=[image] if image else [],
        )


def split_paragraphs(text: str) -> list[str]:
    """Split extracted text into paragraphs, merging very short lines forward.

    trafilatura separates blocks with newlines; headings and one-line fragments
    are merged into the next block so each paragraph is a meaningful anchor.

    Args:
        text: Extracted plain text.

    Returns:
        Non-empty paragraphs in document order.
    """
    paragraphs: list[str] = []
    pending = ""
    for line in (raw.strip() for raw in text.splitlines()):
        if not line:
            continue
        merged = f"{pending} {line}".strip()
        if len(merged) < _MIN_PARAGRAPH_CHARS:
            pending = merged
            continue
        paragraphs.append(merged)
        pending = ""
    if pending:
        paragraphs.append(pending)
    return paragraphs
