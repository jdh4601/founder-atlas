"""Read/write `content/advice/{advice_id}.md`.

Field order in the frontmatter dict matches `docs/content-schema.md` exactly.
`quote` is written but MUST NOT be rendered by the web app (see `CLAUDE.md`);
that rule lives in `web/`, not here — this module just persists it faithfully.
"""

from __future__ import annotations

from pathlib import Path

from founder_atlas_pipeline.frontmatter import dump, parse
from founder_atlas_pipeline.models import AdviceAnchor, AdviceContext, AdviceUnit


def advice_path(content_root: Path, advice_id: str) -> Path:
    """Return the path to one advice unit's Markdown file."""
    return content_root / "advice" / f"{advice_id}.md"


def advice_exists(content_root: Path, advice_id: str) -> bool:
    """Check whether an advice unit has already been written."""
    return advice_path(content_root, advice_id).is_file()


def _advice_to_frontmatter(unit: AdviceUnit) -> dict:
    return {
        "id": unit.id,
        "source": unit.source,
        "category": unit.category,
        "keywords": list(unit.keywords),
        "context": {"stage": list(unit.context.stage), "domain": list(unit.context.domain)},
        "speaker": unit.speaker,
        "claim": unit.claim,
        "quote": unit.quote,
        "anchor": {
            "kind": unit.anchor.kind,
            "start": unit.anchor.start,
            "paragraph": unit.anchor.paragraph,
        },
        "match_score": unit.match_score,
    }


def write_advice(content_root: Path, unit: AdviceUnit) -> None:
    """Write one advice unit's Markdown file.

    Args:
        content_root: The `content/` directory.
        unit: The advice unit to write (`body_ko` is the Markdown body).
    """
    markdown = dump(_advice_to_frontmatter(unit), unit.body_ko)
    advice_path(content_root, unit.id).write_text(markdown, encoding="utf-8")


def read_advice(content_root: Path, advice_id: str) -> AdviceUnit:
    """Read one advice unit's Markdown file back into an `AdviceUnit`.

    Args:
        content_root: The `content/` directory.
        advice_id: The advice id to read.

    Returns:
        The parsed `AdviceUnit`.
    """
    text = advice_path(content_root, advice_id).read_text(encoding="utf-8")
    parsed = parse(text)
    fm = parsed.frontmatter
    context = fm.get("context", {}) or {}
    anchor = fm.get("anchor", {}) or {}
    return AdviceUnit(
        id=fm["id"],
        source=fm["source"],
        category=fm["category"],
        keywords=list(fm.get("keywords", [])),
        context=AdviceContext(
            stage=list(context.get("stage", [])), domain=list(context.get("domain", []))
        ),
        speaker=fm.get("speaker"),
        claim=fm["claim"],
        quote=fm["quote"],
        anchor=AdviceAnchor(
            kind=anchor["kind"], start=anchor.get("start"), paragraph=anchor.get("paragraph")
        ),
        match_score=fm["match_score"],
        body_ko=parsed.body.strip(),
    )


def list_advice_ids(content_root: Path, source_id: str | None = None) -> list[str]:
    """List advice ids, optionally filtered to one source.

    Args:
        content_root: The `content/` directory.
        source_id: If given, only advice ids for this source id are returned.

    Returns:
        Sorted list of advice ids.
    """
    advice_dir = content_root / "advice"
    ids = sorted(p.stem for p in advice_dir.glob("*.md"))
    if source_id is None:
        return ids
    prefix = f"{source_id}--"
    return [i for i in ids if i.startswith(prefix)]


def list_all_advice(content_root: Path) -> list[AdviceUnit]:
    """Read every advice unit under `content/advice/`.

    Args:
        content_root: The `content/` directory.

    Returns:
        All advice units, in id-sorted order.
    """
    return [read_advice(content_root, advice_id) for advice_id in list_advice_ids(content_root)]
