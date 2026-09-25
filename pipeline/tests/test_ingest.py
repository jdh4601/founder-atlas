"""Tests for `atlas ingest`: URL -> content/sources/{id}.md + .transcript.json.

Fetchers are faked so tests never touch the network.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from founder_atlas_pipeline.ingest.fetchers import (
    Article,
    FetchError,
    VideoMetadata,
)
from founder_atlas_pipeline.ingest.pipeline import (
    UnsupportedSourceError,
    infer_origin,
    ingest_many,
    ingest_url,
    parse_youtube_id,
)
from founder_atlas_pipeline.models import TranscriptSegment
from founder_atlas_pipeline.sources import read_source, read_transcript, source_exists


class FakeYouTube:
    def __init__(self, segments: list[TranscriptSegment] | None = None) -> None:
        self.segments = segments if segments is not None else [
            TranscriptSegment(start=0.0, duration=2.0, text="charge more"),
            TranscriptSegment(start=2.0, duration=3.0, text="than you think"),
        ]
        self.metadata_calls = 0

    def fetch_metadata(self, video_id: str) -> VideoMetadata:
        self.metadata_calls += 1
        return VideoMetadata(
            youtube_id=video_id,
            title="How to Price Your Product",
            published="2024-03-01",
            thumbnail=f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
        )

    def fetch_segments(self, video_id: str) -> list[TranscriptSegment]:
        if not self.segments:
            raise FetchError(f"no English transcript for {video_id}")
        return self.segments


class FakeWeb:
    def fetch_article(self, url: str) -> Article:
        return Article(
            title="Do Things that Don't Scale",
            published="2013-07-01",
            paragraphs=["One of the most common types of advice...", "Recruit users manually."],
            images=["https://paulgraham.com/og.png"],
        )


YT_URL = "https://www.youtube.com/watch?v=abcDEF12345"


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://www.youtube.com/watch?v=abcDEF12345", "abcDEF12345"),
        ("https://youtu.be/abcDEF12345?t=30", "abcDEF12345"),
        ("https://www.youtube.com/watch?list=PL1&v=abcDEF12345", "abcDEF12345"),
        ("https://paulgraham.com/ds.html", None),
    ],
)
def test_parse_youtube_id_handles_common_url_shapes(url: str, expected: str | None) -> None:
    assert parse_youtube_id(url) == expected


@pytest.mark.parametrize(
    ("url", "override", "expected"),
    [
        (YT_URL, None, "yc-youtube"),
        (YT_URL, "lightcone", "lightcone"),
        ("https://paulgraham.com/ds.html", None, "paul-graham"),
        ("https://a16z.com/some-post/", None, "a16z"),
    ],
)
def test_infer_origin_uses_host_and_override(url: str, override: str | None, expected: str) -> None:
    assert infer_origin(url, override) == expected


def test_infer_origin_rejects_unknown_host() -> None:
    with pytest.raises(UnsupportedSourceError):
        infer_origin("https://example.com/post", None)


def test_ingest_video_writes_source_and_segments(content_root: Path) -> None:
    result = ingest_url(
        content_root, YT_URL, youtube=FakeYouTube(), web=FakeWeb(), today="2026-09-25"
    )

    assert result.status == "written"
    assert result.source_id == "yc-youtube-how-to-price-your-product"
    meta = read_source(content_root, result.source_id)
    assert meta.format == "video"
    assert meta.youtube_id == "abcDEF12345"
    assert meta.url == YT_URL
    assert meta.thumbnail == "https://i.ytimg.com/vi/abcDEF12345/hqdefault.jpg"
    assert meta.ingested_at == "2026-09-25"
    transcript = read_transcript(content_root, result.source_id)
    assert transcript.kind == "segments"
    assert [s.text for s in transcript.segments] == ["charge more", "than you think"]


def test_ingest_essay_writes_paragraphs_and_images(content_root: Path) -> None:
    result = ingest_url(
        content_root, "https://paulgraham.com/ds.html", youtube=FakeYouTube(), web=FakeWeb()
    )

    meta = read_source(content_root, result.source_id)
    assert result.source_id == "paul-graham-do-things-that-don-t-scale"
    assert meta.format == "essay"
    assert meta.youtube_id is None
    assert meta.images == ["https://paulgraham.com/og.png"]
    assert meta.thumbnail == "https://paulgraham.com/og.png"
    assert read_transcript(content_root, result.source_id).kind == "paragraphs"


def test_ingest_a16z_is_blog_format(content_root: Path) -> None:
    result = ingest_url(content_root, "https://a16z.com/post/", youtube=FakeYouTube(), web=FakeWeb())
    assert read_source(content_root, result.source_id).format == "blog"


def test_ingest_skips_existing_source_unless_forced(content_root: Path) -> None:
    ingest_url(content_root, YT_URL, youtube=FakeYouTube(), web=FakeWeb())

    again = ingest_url(content_root, YT_URL, youtube=FakeYouTube(), web=FakeWeb())
    forced = ingest_url(content_root, YT_URL, youtube=FakeYouTube(), web=FakeWeb(), force=True)

    assert again.status == "skipped"
    assert forced.status == "written"


def test_ingest_many_reports_failures_without_stopping_batch(content_root: Path) -> None:
    urls = [YT_URL, "https://example.com/unsupported", "https://paulgraham.com/ds.html"]

    outcomes = ingest_many(content_root, urls, youtube=FakeYouTube(), web=FakeWeb())

    assert [o.status for o in outcomes] == ["written", "failed", "written"]
    assert "example.com" in (outcomes[1].error or "")
    assert source_exists(content_root, "paul-graham-do-things-that-don-t-scale")


def test_ingest_many_marks_missing_transcript_as_failed(content_root: Path) -> None:
    outcomes = ingest_many(content_root, [YT_URL], youtube=FakeYouTube(segments=[]), web=FakeWeb())

    assert outcomes[0].status == "failed"
    assert "transcript" in (outcomes[0].error or "")
    assert not list((content_root / "sources").glob("*.md"))


def test_split_paragraphs_merges_short_heading_into_next_block() -> None:
    from founder_atlas_pipeline.ingest.fetchers import split_paragraphs

    text = "Recruit\n\nThe most common unscalable thing founders have to do is recruit users.\n\nshort tail"

    assert split_paragraphs(text) == [
        "Recruit The most common unscalable thing founders have to do is recruit users.",
        "short tail",
    ]
