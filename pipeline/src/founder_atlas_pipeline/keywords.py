"""Read/write `content/keywords/{slug}.md`.

Field order in the frontmatter dict matches `docs/content-schema.md` exactly.
`reviewed: true` pages are treated as human-approved by `build_pages/pipeline.py`
and must not be silently overwritten (see that module's `--force` handling).
"""

from __future__ import annotations

from pathlib import Path

from founder_atlas_pipeline.frontmatter import dump, parse
from founder_atlas_pipeline.models import KeywordImage, KeywordPage


def keyword_path(content_root: Path, slug: str) -> Path:
    """Return the path to one keyword page's Markdown file."""
    return content_root / "keywords" / f"{slug}.md"


def keyword_exists(content_root: Path, slug: str) -> bool:
    """Check whether a keyword page has already been written."""
    return keyword_path(content_root, slug).is_file()


def _keyword_to_frontmatter(page: KeywordPage) -> dict:
    return {
        "slug": page.slug,
        "title": page.title,
        "category": page.category,
        "summary": page.summary,
        "reviewed": page.reviewed,
        "advice": list(page.advice),
        "images": [{"src": i.src, "alt": i.alt, "source": i.source} for i in page.images],
        "updated_at": page.updated_at,
    }


def write_keyword(content_root: Path, page: KeywordPage) -> None:
    """Write one keyword page's Markdown file.

    Args:
        content_root: The `content/` directory.
        page: The keyword page to write (`body_ko` is the Markdown body).
    """
    markdown = dump(_keyword_to_frontmatter(page), page.body_ko)
    keyword_path(content_root, page.slug).write_text(markdown, encoding="utf-8")


def read_keyword(content_root: Path, slug: str) -> KeywordPage:
    """Read one keyword page's Markdown file back into a `KeywordPage`.

    Args:
        content_root: The `content/` directory.
        slug: The keyword slug to read.

    Returns:
        The parsed `KeywordPage`.
    """
    text = keyword_path(content_root, slug).read_text(encoding="utf-8")
    parsed = parse(text)
    fm = parsed.frontmatter
    images = [
        KeywordImage(src=i["src"], alt=i["alt"], source=i["source"]) for i in fm.get("images", [])
    ]
    return KeywordPage(
        slug=fm["slug"],
        title=fm["title"],
        category=fm["category"],
        summary=fm["summary"],
        reviewed=bool(fm.get("reviewed", False)),
        advice=list(fm.get("advice", [])),
        images=images,
        updated_at=fm["updated_at"],
        body_ko=parsed.body.strip(),
    )


def list_keyword_slugs(content_root: Path) -> list[str]:
    """List all written keyword slugs, sorted.

    Args:
        content_root: The `content/` directory.

    Returns:
        Sorted list of keyword slugs.
    """
    keywords_dir = content_root / "keywords"
    return sorted(p.stem for p in keywords_dir.glob("*.md"))
