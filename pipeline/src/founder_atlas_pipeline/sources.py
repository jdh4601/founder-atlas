"""Read/write `content/sources/{source_id}.md` and `.transcript.json`.

Field order in the frontmatter dict matches `docs/content-schema.md` exactly.
`youtube_id` is only present in the dict when the source actually has one
(video/podcast hosted on YouTube) — the schema marks it as conditional,
unlike `published`/`thumbnail`, which the schema says "may be null".
"""

from __future__ import annotations

import json
from pathlib import Path

from founder_atlas_pipeline.frontmatter import dump, parse
from founder_atlas_pipeline.models import SourceMeta, Transcript, TranscriptSegment


def source_markdown_path(content_root: Path, source_id: str) -> Path:
    """Return the path to a source's Markdown metadata file."""
    return content_root / "sources" / f"{source_id}.md"


def source_transcript_path(content_root: Path, source_id: str) -> Path:
    """Return the path to a source's raw transcript JSON file."""
    return content_root / "sources" / f"{source_id}.transcript.json"


def source_exists(content_root: Path, source_id: str) -> bool:
    """Check whether a source has already been ingested.

    Args:
        content_root: The `content/` directory.
        source_id: The source id to check.

    Returns:
        True if `content/sources/{source_id}.md` already exists.
    """
    return source_markdown_path(content_root, source_id).is_file()


def _source_to_frontmatter(meta: SourceMeta) -> dict:
    frontmatter = {
        "id": meta.id,
        "title": meta.title,
        "title_ko": meta.title_ko,
        "url": meta.url,
        "origin": meta.origin,
        "format": meta.format,
    }
    if meta.youtube_id is not None:
        frontmatter["youtube_id"] = meta.youtube_id
    frontmatter["published"] = meta.published
    frontmatter["speakers"] = list(meta.speakers)
    frontmatter["thumbnail"] = meta.thumbnail
    frontmatter["images"] = list(meta.images)
    frontmatter["ingested_at"] = meta.ingested_at
    return frontmatter


def write_source(content_root: Path, meta: SourceMeta, transcript: Transcript) -> None:
    """Write a source's Markdown metadata file and transcript JSON.

    Args:
        content_root: The `content/` directory.
        meta: The source's metadata (Korean summary is the Markdown body).
        transcript: The raw transcript (segments or paragraphs).
    """
    markdown = dump(_source_to_frontmatter(meta), meta.summary_ko)
    source_markdown_path(content_root, meta.id).write_text(markdown, encoding="utf-8")

    payload: dict = {"kind": transcript.kind}
    if transcript.kind == "segments":
        payload["segments"] = [
            {"start": s.start, "duration": s.duration, "text": s.text} for s in transcript.segments
        ]
    else:
        payload["paragraphs"] = list(transcript.paragraphs)
    transcript_path = source_transcript_path(content_root, meta.id)
    transcript_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_source(content_root: Path, source_id: str) -> SourceMeta:
    """Read a source's Markdown metadata file back into a `SourceMeta`.

    Args:
        content_root: The `content/` directory.
        source_id: The source id to read.

    Returns:
        The parsed `SourceMeta`.
    """
    text = source_markdown_path(content_root, source_id).read_text(encoding="utf-8")
    parsed = parse(text)
    fm = parsed.frontmatter
    return SourceMeta(
        id=fm["id"],
        title=fm["title"],
        title_ko=fm["title_ko"],
        url=fm["url"],
        origin=fm["origin"],
        format=fm["format"],
        youtube_id=fm.get("youtube_id"),
        published=fm.get("published"),
        speakers=list(fm.get("speakers", [])),
        thumbnail=fm.get("thumbnail"),
        images=list(fm.get("images", [])),
        ingested_at=fm["ingested_at"],
        summary_ko=parsed.body.strip(),
    )


def read_transcript(content_root: Path, source_id: str) -> Transcript:
    """Read a source's transcript JSON file.

    Args:
        content_root: The `content/` directory.
        source_id: The source id to read.

    Returns:
        The parsed `Transcript`.
    """
    payload = json.loads(source_transcript_path(content_root, source_id).read_text(encoding="utf-8"))
    kind = payload["kind"]
    segments = [
        TranscriptSegment(start=s["start"], duration=s["duration"], text=s["text"])
        for s in payload.get("segments", [])
    ]
    paragraphs = list(payload.get("paragraphs", []))
    return Transcript(kind=kind, segments=segments, paragraphs=paragraphs)


def list_source_ids(content_root: Path) -> list[str]:
    """List all ingested source ids, sorted.

    Args:
        content_root: The `content/` directory.

    Returns:
        Sorted list of source ids.
    """
    sources_dir = content_root / "sources"
    return sorted(p.stem for p in sources_dir.glob("*.md"))
