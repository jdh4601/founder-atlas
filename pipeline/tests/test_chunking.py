"""Tests for transcript chunking used by the extract pipeline."""

from __future__ import annotations

from founder_atlas_pipeline.chunking import chunk_transcript
from founder_atlas_pipeline.models import Transcript, TranscriptSegment


def _segments(n: int, text_len: int = 20) -> list[TranscriptSegment]:
    return [
        TranscriptSegment(start=float(i), duration=1.0, text="x" * text_len) for i in range(n)
    ]


def test_short_transcript_produces_a_single_chunk() -> None:
    transcript = Transcript(kind="segments", segments=_segments(3, text_len=10))
    chunks = chunk_transcript(transcript, max_chars=1000)
    assert len(chunks) == 1
    assert chunks[0].item_start == 0
    assert chunks[0].item_end == 3


def test_long_transcript_splits_into_multiple_chunks() -> None:
    transcript = Transcript(kind="segments", segments=_segments(10, text_len=50))
    chunks = chunk_transcript(transcript, max_chars=150, overlap_items=0)
    assert len(chunks) > 1
    # Every item appears in exactly one chunk when overlap is 0.
    covered = [seg for chunk in chunks for seg in range(chunk.item_start, chunk.item_end)]
    assert covered == list(range(10))


def test_chunk_never_splits_a_single_segment_across_two_chunks() -> None:
    transcript = Transcript(kind="segments", segments=_segments(5, text_len=50))
    chunks = chunk_transcript(transcript, max_chars=60, overlap_items=0)
    for chunk in chunks:
        assert chunk.item_end > chunk.item_start


def test_overlap_repeats_the_boundary_item_in_the_next_chunk() -> None:
    transcript = Transcript(kind="segments", segments=_segments(6, text_len=40))
    chunks = chunk_transcript(transcript, max_chars=90, overlap_items=1)
    assert len(chunks) > 1
    for prev, nxt in zip(chunks, chunks[1:]):
        assert nxt.item_start == prev.item_end - 1


def test_chunking_terminates_when_every_item_alone_exceeds_max_chars() -> None:
    """A degenerate max_chars (smaller than one item) must not infinite-loop."""
    transcript = Transcript(kind="segments", segments=_segments(4, text_len=200))
    chunks = chunk_transcript(transcript, max_chars=10, overlap_items=1)
    assert len(chunks) == 4
    covered_starts = [c.item_start for c in chunks]
    assert covered_starts == [0, 1, 2, 3]


def test_paragraph_transcript_chunks_by_paragraph() -> None:
    transcript = Transcript(kind="paragraphs", paragraphs=["a" * 50] * 5)
    chunks = chunk_transcript(transcript, max_chars=120, overlap_items=0)
    assert len(chunks) > 1
    assert all(c.text for c in chunks)


def test_empty_transcript_produces_no_chunks() -> None:
    transcript = Transcript(kind="segments", segments=[])
    assert chunk_transcript(transcript, max_chars=1000) == []
