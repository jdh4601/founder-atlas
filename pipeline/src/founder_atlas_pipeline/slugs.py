"""Slug and id generation.

Slugs are lowercase kebab-case ASCII (per `docs/content-schema.md`).
`source_id` = `{origin}-{slug}`. `advice_id` = `{source_id}--{nn}` (two-digit index).
"""

from __future__ import annotations

import re
import unicodedata

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def slugify(text: str, max_words: int = 8) -> str:
    """Convert arbitrary text into a lowercase kebab-case ASCII slug.

    Args:
        text: Source text, e.g. a video/article title.
        max_words: Maximum number of words kept, to keep slugs short.

    Returns:
        A lowercase kebab-case ASCII slug. Never empty ("untitled" fallback).
    """
    normalized = unicodedata.normalize("NFKD", text)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_only.lower()
    dashed = _NON_ALNUM.sub("-", lowered).strip("-")
    words = [w for w in dashed.split("-") if w]
    slug = "-".join(words[:max_words])
    return slug or "untitled"


def make_source_id(origin: str, title: str) -> str:
    """Build the `source_id` for a source: `{origin}-{slug(title)}`.

    Args:
        origin: One of yc-youtube | lightcone | paul-graham | a16z.
        title: The source's original title.

    Returns:
        The source id, e.g. `yc-youtube-how-to-price-your-product`.
    """
    return f"{origin}-{slugify(title)}"


def make_advice_id(source_id: str, index: int) -> str:
    """Build the `advice_id` for the `index`-th advice unit of a source.

    Args:
        source_id: The parent source's id.
        index: 1-based index of this advice unit within the source.

    Returns:
        The advice id, e.g. `yc-youtube-how-to-price-your-product--03`.

    Raises:
        ValueError: If `index` is not a positive integer that fits two digits.
    """
    if index < 1 or index > 99:
        raise ValueError(f"advice index must be in 1..99, got {index}")
    return f"{source_id}--{index:02d}"


def next_advice_index(existing_ids: list[str]) -> int:
    """Return the next free 1-based advice index for a source.

    Args:
        existing_ids: Advice ids already written for one source
            (e.g. `["src--01", "src--02"]`).

    Returns:
        The next unused index, e.g. `3` for the example above.
    """
    used = set()
    for advice_id in existing_ids:
        suffix = advice_id.rsplit("--", 1)[-1]
        if suffix.isdigit():
            used.add(int(suffix))
    index = 1
    while index in used:
        index += 1
    return index
