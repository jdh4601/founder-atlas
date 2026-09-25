"""Quote verification: fuzzy-match an LLM-proposed quote against raw transcript text.

Per `CLAUDE.md`: timestamps come from code, never the LLM. This module is
the only place that computes an `AdviceAnchor` — it never trusts a
timestamp/paragraph index the model might have guessed.

YouTube auto-captions are noisy (dropped punctuation, minor misspellings),
so matching normalizes case/whitespace/punctuation and uses a sliding
partial-ratio alignment (`rapidfuzz.fuzz.partial_ratio_alignment`) rather
than an exact or full-string comparison.
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass

from rapidfuzz import fuzz

from founder_atlas_pipeline.models import AdviceAnchor, Transcript

_SEPARATOR = " "


@dataclass(frozen=True)
class QuoteMatch:
    """Result of fuzzy-matching a quote against a transcript.

    Attributes:
        score: rapidfuzz partial-ratio score (0-100).
        anchor: The computed anchor. Only trustworthy when `score >= 90`
            (callers are responsible for enforcing that threshold).
    """

    score: float
    anchor: AdviceAnchor


def _normalize_with_map(text: str) -> tuple[str, list[int]]:
    """Lowercase, collapse whitespace/punctuation to single spaces, and track original offsets.

    Args:
        text: Raw text to normalize.

    Returns:
        A tuple of (normalized text, list where `map[i]` is the index in
        `text` that produced `normalized[i]`).
    """
    chars: list[str] = []
    index_map: list[int] = []
    previous_was_space = True  # collapse a leading run of separators too
    for i, ch in enumerate(text):
        if ch.isalnum():
            chars.append(ch.lower())
            index_map.append(i)
            previous_was_space = False
        elif not previous_was_space:
            chars.append(" ")
            index_map.append(i)
            previous_was_space = True
    while chars and chars[-1] == " ":
        chars.pop()
        index_map.pop()
    return "".join(chars), index_map


def _boundaries(lengths: list[int]) -> list[int]:
    """Return cumulative start offsets of each item once joined by `_SEPARATOR`."""
    bounds = [0]
    for length in lengths:
        bounds.append(bounds[-1] + length + len(_SEPARATOR))
    return bounds


def _segment_index_for_offset(boundaries: list[int], offset: int) -> int:
    """Find which item (0-based) a raw joined-text offset falls into."""
    index = bisect.bisect_right(boundaries, offset) - 1
    return max(0, min(index, len(boundaries) - 2))


def _match_against_texts(quote: str, texts: list[str]) -> tuple[float, int]:
    """Fuzzy-match `quote` against `texts` joined by a separator.

    Args:
        quote: The candidate quote.
        texts: Ordered list of segment/paragraph texts to search across.

    Returns:
        A tuple of (score, item_index) where `item_index` is the item the
        match's start offset falls into. `(0.0, 0)` when `texts` is empty.
    """
    if not texts:
        return 0.0, 0

    raw_full_text = _SEPARATOR.join(texts)
    boundaries = _boundaries([len(t) for t in texts])

    normalized_quote, _ = _normalize_with_map(quote)
    normalized_full, full_map = _normalize_with_map(raw_full_text)

    if not normalized_quote or not normalized_full:
        return 0.0, 0

    alignment = fuzz.partial_ratio_alignment(normalized_quote, normalized_full)
    dest_start = min(alignment.dest_start, len(full_map) - 1)
    raw_offset = full_map[dest_start]
    item_index = _segment_index_for_offset(boundaries, raw_offset)
    return alignment.score, item_index


def verify_quote_against_transcript(quote: str, transcript: Transcript) -> QuoteMatch:
    """Fuzzy-match `quote` against a transcript and compute its anchor.

    Args:
        quote: The verbatim English quote an LLM proposed.
        transcript: The source's raw transcript (segments or paragraphs).

    Returns:
        A `QuoteMatch` with the match score and a code-computed anchor.
        Callers must still enforce `score >= 90` before trusting the anchor.
    """
    if transcript.kind == "segments":
        texts = [s.text for s in transcript.segments]
        score, index = _match_against_texts(quote, texts)
        start = int(transcript.segments[index].start) if transcript.segments else 0
        return QuoteMatch(score=score, anchor=AdviceAnchor(kind="timestamp", start=start))

    texts = list(transcript.paragraphs)
    score, index = _match_against_texts(quote, texts)
    return QuoteMatch(score=score, anchor=AdviceAnchor(kind="paragraph", paragraph=index))
