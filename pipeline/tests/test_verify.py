"""Tests for quote verification + timestamp/paragraph anchor mapping.

This is the core trust boundary of the pipeline (per CLAUDE.md, timestamps
must come from code, never the LLM), so it gets the heaviest coverage:
noisy captions, quotes spanning two segments, and no-match cases.
"""

from __future__ import annotations

from founder_atlas_pipeline.models import Transcript, TranscriptSegment
from founder_atlas_pipeline.verify import verify_quote_against_transcript

SEGMENTS = [
    TranscriptSegment(start=0.0, duration=5.0, text="Welcome back to the show today."),
    TranscriptSegment(start=5.0, duration=6.0, text="Charge more than you think you should."),
    TranscriptSegment(start=11.0, duration=4.0, text="That is the whole pricing lesson."),
]
SEGMENT_TRANSCRIPT = Transcript(kind="segments", segments=SEGMENTS)

PARAGRAPHS = [
    "This essay is about how founders think about pricing.",
    "Charge more than you think you should, especially early on.",
    "That's really the whole lesson in one sentence.",
]
PARAGRAPH_TRANSCRIPT = Transcript(kind="paragraphs", paragraphs=PARAGRAPHS)


def test_exact_quote_maps_to_its_segment_start() -> None:
    result = verify_quote_against_transcript(
        "Charge more than you think you should.", SEGMENT_TRANSCRIPT
    )
    assert result.score >= 90
    assert result.anchor.kind == "timestamp"
    assert result.anchor.start == 5
    assert result.anchor.paragraph is None


def test_noisy_caption_quote_still_matches_above_threshold() -> None:
    """YouTube auto-captions drop punctuation and sometimes misspell words."""
    noisy_quote = "charge more then you think you shuld"
    result = verify_quote_against_transcript(noisy_quote, SEGMENT_TRANSCRIPT)
    assert result.score >= 90
    assert result.anchor.kind == "timestamp"
    assert result.anchor.start == 5


def test_quote_spanning_two_segments_anchors_to_the_starting_segment() -> None:
    spanning_quote = "today. Charge more than you think"
    result = verify_quote_against_transcript(spanning_quote, SEGMENT_TRANSCRIPT)
    assert result.score >= 90
    # The quote begins inside the first segment ("...today."), so the anchor
    # must point at segment 0's start, not segment 1's.
    assert result.anchor.start == 0


def test_completely_unrelated_quote_scores_low() -> None:
    result = verify_quote_against_transcript(
        "Never trust a founder who wears a suit to a hackathon.", SEGMENT_TRANSCRIPT
    )
    assert result.score < 90


def test_empty_transcript_segments_score_zero_and_do_not_raise() -> None:
    empty = Transcript(kind="segments", segments=[])
    result = verify_quote_against_transcript("anything", empty)
    assert result.score == 0.0
    assert result.anchor.kind == "timestamp"


def test_paragraph_transcript_maps_to_correct_paragraph_index() -> None:
    result = verify_quote_against_transcript(
        "Charge more than you think you should, especially early on.",
        PARAGRAPH_TRANSCRIPT,
    )
    assert result.score >= 90
    assert result.anchor.kind == "paragraph"
    assert result.anchor.paragraph == 1
    assert result.anchor.start is None


def test_picks_the_best_matching_segment_among_distractors() -> None:
    segments = [
        TranscriptSegment(start=0.0, duration=3.0, text="Pricing is hard for everyone."),
        TranscriptSegment(start=3.0, duration=3.0, text="Charge more than you think you should."),
        TranscriptSegment(start=6.0, duration=3.0, text="Pricing is hard for everyone else too."),
    ]
    transcript = Transcript(kind="segments", segments=segments)
    result = verify_quote_against_transcript(
        "Charge more than you think you should.", transcript
    )
    assert result.anchor.start == 3


def test_score_is_a_percentage_between_0_and_100() -> None:
    result = verify_quote_against_transcript(
        "Charge more than you think you should.", SEGMENT_TRANSCRIPT
    )
    assert 0.0 <= result.score <= 100.0
