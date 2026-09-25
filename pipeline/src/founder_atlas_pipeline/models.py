"""Data containers mirroring `docs/content-schema.md`.

These are the shared shapes passed between pipeline stages. Field names and
nesting match the schema exactly so frontmatter serialization is a direct
mapping (see `frontmatter.py`).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TranscriptSegment:
    """One caption segment of a video/podcast transcript.

    Attributes:
        start: Segment start time in seconds.
        duration: Segment duration in seconds.
        text: Caption text for this segment.
    """

    start: float
    duration: float
    text: str


@dataclass(frozen=True)
class Transcript:
    """Raw source text: either video segments or essay/blog paragraphs.

    Exactly one of `segments` / `paragraphs` is populated, matching
    `sources/{source_id}.transcript.json` in the schema.
    """

    kind: str  # "segments" | "paragraphs"
    segments: list[TranscriptSegment] = field(default_factory=list)
    paragraphs: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SourceMeta:
    """Metadata for `content/sources/{source_id}.md`."""

    id: str
    title: str
    title_ko: str
    url: str
    origin: str  # yc-youtube | lightcone | paul-graham | a16z
    format: str  # video | essay | blog | podcast
    published: str | None
    speakers: list[str]
    thumbnail: str | None
    images: list[str]
    ingested_at: str
    summary_ko: str
    youtube_id: str | None = None


@dataclass(frozen=True)
class AdviceContext:
    """"My situation" filter attributes an advice unit applies to."""

    stage: list[str] = field(default_factory=list)
    domain: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AdviceAnchor:
    """Location of the verified quote inside its source, computed by code."""

    kind: str  # "timestamp" | "paragraph"
    start: int | None = None
    paragraph: int | None = None


@dataclass(frozen=True)
class AdviceUnit:
    """One advice unit: `content/advice/{advice_id}.md`."""

    id: str
    source: str
    category: str
    keywords: list[str]
    context: AdviceContext
    speaker: str | None
    claim: str
    quote: str
    anchor: AdviceAnchor
    match_score: float
    body_ko: str


@dataclass(frozen=True)
class KeywordImage:
    """One image reference on a keyword page."""

    src: str
    alt: str
    source: str


@dataclass(frozen=True)
class KeywordPage:
    """One keyword page: `content/keywords/{slug}.md`."""

    slug: str
    title: str
    category: str
    summary: str
    reviewed: bool
    advice: list[str]
    images: list[KeywordImage]
    updated_at: str
    body_ko: str
