"""Tests for content/sources/ read/write."""

from __future__ import annotations

from pathlib import Path

from founder_atlas_pipeline.models import SourceMeta, Transcript, TranscriptSegment
from founder_atlas_pipeline.sources import (
    read_source,
    read_transcript,
    source_exists,
    write_source,
)


def _video_meta(**overrides) -> SourceMeta:
    defaults = dict(
        id="yc-youtube-how-to-price-your-product",
        title="How to Price Your Product",
        title_ko="제품 가격을 정하는 법",
        url="https://www.youtube.com/watch?v=abc123",
        origin="yc-youtube",
        format="video",
        youtube_id="abc123",
        published="2024-03-01",
        speakers=["Kevin Hale"],
        thumbnail="https://i.ytimg.com/vi/abc123/hqdefault.jpg",
        images=[],
        ingested_at="2026-09-25",
        summary_ko="한국어 요약 한 문단.",
    )
    defaults.update(overrides)
    return SourceMeta(**defaults)


def test_write_then_read_video_source_round_trips(content_root: Path) -> None:
    meta = _video_meta()
    transcript = Transcript(
        kind="segments",
        segments=[TranscriptSegment(start=12.4, duration=3.1, text="Charge more.")],
    )
    write_source(content_root, meta, transcript)

    assert source_exists(content_root, meta.id)
    loaded = read_source(content_root, meta.id)
    assert loaded == meta

    loaded_transcript = read_transcript(content_root, meta.id)
    assert loaded_transcript.kind == "segments"
    assert loaded_transcript.segments[0].start == 12.4


def test_essay_source_omits_youtube_id_key(content_root: Path) -> None:
    meta = _video_meta(
        id="paul-graham-do-things",
        origin="paul-graham",
        format="essay",
        youtube_id=None,
        url="https://paulgraham.com/do.html",
        thumbnail=None,
    )
    transcript = Transcript(kind="paragraphs", paragraphs=["첫 문단.", "둘째 문단."])
    write_source(content_root, meta, transcript)

    text = (content_root / "sources" / f"{meta.id}.md").read_text(encoding="utf-8")
    assert "youtube_id" not in text

    loaded = read_source(content_root, meta.id)
    assert loaded.youtube_id is None


def test_source_exists_is_false_before_write(content_root: Path) -> None:
    assert source_exists(content_root, "yc-youtube-nonexistent") is False
