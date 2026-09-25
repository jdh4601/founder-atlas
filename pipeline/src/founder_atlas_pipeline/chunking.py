"""Split long transcripts into LLM-sized chunks for `atlas extract`.

Chunks never split a single segment/paragraph, and adjacent chunks overlap
by `overlap_items` items so a quote sitting right at a chunk boundary is
still visible to the model in at least one chunk. Verification (`verify.py`)
always runs against the full transcript, not a chunk, so chunk boundaries
cannot affect anchor correctness — only extraction recall.
"""

from __future__ import annotations

from dataclasses import dataclass

from founder_atlas_pipeline.models import Transcript

DEFAULT_MAX_CHARS = 6000
DEFAULT_OVERLAP_ITEMS = 1


@dataclass(frozen=True)
class TranscriptChunk:
    """One chunk of a transcript, ready to hand to the extraction prompt.

    Attributes:
        index: 0-based chunk index.
        text: The chunk's text, one segment/paragraph per line.
        item_start: Inclusive start index into the transcript's item list.
        item_end: Exclusive end index into the transcript's item list.
    """

    index: int
    text: str
    item_start: int
    item_end: int


def _items(transcript: Transcript) -> list[str]:
    if transcript.kind == "segments":
        return [s.text for s in transcript.segments]
    return list(transcript.paragraphs)


def chunk_transcript(
    transcript: Transcript,
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap_items: int = DEFAULT_OVERLAP_ITEMS,
) -> list[TranscriptChunk]:
    """Split a transcript into overlapping chunks under `max_chars` each.

    Args:
        transcript: The transcript to chunk (segments or paragraphs).
        max_chars: Soft character budget per chunk. A single item longer
            than this still gets its own chunk (never split mid-item).
        overlap_items: How many trailing items of a chunk to repeat as the
            leading items of the next chunk.

    Returns:
        Ordered list of `TranscriptChunk`. Empty if the transcript has no items.
    """
    items = _items(transcript)
    if not items:
        return []

    chunks: list[TranscriptChunk] = []
    start = 0
    n = len(items)
    while start < n:
        end = start
        length = 0
        while end < n:
            item_len = len(items[end]) + 1
            if length + item_len > max_chars and end > start:
                break
            length += item_len
            end += 1

        chunks.append(
            TranscriptChunk(
                index=len(chunks),
                text="\n".join(items[start:end]),
                item_start=start,
                item_end=end,
            )
        )
        if end >= n:
            break

        next_start = end - overlap_items
        start = next_start if next_start > start else end

    return chunks
