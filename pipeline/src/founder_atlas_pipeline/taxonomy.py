"""Load and validate `content/taxonomy.yaml` and `content/profile.yaml`.

`taxonomy.yaml` and `profile.yaml` are hand-edited by a human (per the task
brief, the pipeline must never write to them) — this module only reads and
validates them.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

MAX_KEYWORDS_PER_CATEGORY = 20
REQUIRED_CATEGORY_COUNT = 8

VALID_STAGES = {"idea", "pre-seed", "seed", "series-a", "growth"}
VALID_DOMAINS = {"ai", "b2b", "b2c", "saas", "marketplace", "devtools", "consumer", "hardware"}


class TaxonomyError(Exception):
    """Raised when `taxonomy.yaml` violates the schema's fixed rules."""


@dataclass(frozen=True)
class Keyword:
    """One keyword entry inside a category."""

    slug: str
    title: str


@dataclass(frozen=True)
class Category:
    """One of the 8 fixed taxonomy categories."""

    slug: str
    title: str
    color: str
    keywords: list[Keyword]


@dataclass(frozen=True)
class Taxonomy:
    """The full parsed and validated taxonomy."""

    categories: list[Category]

    def category_slugs(self) -> set[str]:
        """Return the set of all category slugs."""
        return {c.slug for c in self.categories}

    def keyword_slugs(self) -> set[str]:
        """Return the set of all keyword slugs across every category."""
        return {kw.slug for c in self.categories for kw in c.keywords}

    def category_for_keyword(self, keyword_slug: str) -> Category | None:
        """Find the category that owns a given keyword slug.

        Args:
            keyword_slug: A keyword slug to look up.

        Returns:
            The owning `Category`, or `None` if the slug is unknown.
        """
        for category in self.categories:
            if any(kw.slug == keyword_slug for kw in category.keywords):
                return category
        return None

    def keywords_for_category(self, category_slug: str) -> list[Keyword]:
        """Return the keywords declared for a category slug.

        Args:
            category_slug: A category slug to look up.

        Returns:
            The category's keywords, or an empty list if the slug is unknown.
        """
        for category in self.categories:
            if category.slug == category_slug:
                return category.keywords
        return []


def load_taxonomy(path: Path) -> Taxonomy:
    """Load and validate `taxonomy.yaml`.

    Args:
        path: Path to `content/taxonomy.yaml`.

    Returns:
        The parsed and validated `Taxonomy`.

    Raises:
        TaxonomyError: If the file violates a fixed rule (category count,
            per-category keyword cap, or global keyword-slug uniqueness).
    """
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    raw_categories = raw.get("categories", [])

    categories = [
        Category(
            slug=c["slug"],
            title=c["title"],
            color=c["color"],
            keywords=[Keyword(slug=kw["slug"], title=kw["title"]) for kw in c.get("keywords", [])],
        )
        for c in raw_categories
    ]

    if len(categories) != REQUIRED_CATEGORY_COUNT:
        raise TaxonomyError(
            f"taxonomy.yaml must have exactly {REQUIRED_CATEGORY_COUNT} categories, "
            f"got {len(categories)}"
        )

    seen_keyword_slugs: dict[str, str] = {}
    for category in categories:
        if len(category.keywords) > MAX_KEYWORDS_PER_CATEGORY:
            raise TaxonomyError(
                f"category '{category.slug}' has {len(category.keywords)} keywords, "
                f"max is {MAX_KEYWORDS_PER_CATEGORY}"
            )
        for keyword in category.keywords:
            if keyword.slug in seen_keyword_slugs:
                raise TaxonomyError(
                    f"keyword slug '{keyword.slug}' is used in both "
                    f"'{seen_keyword_slugs[keyword.slug]}' and '{category.slug}' "
                    "(keyword slugs must be globally unique)"
                )
            seen_keyword_slugs[keyword.slug] = category.slug

    return Taxonomy(categories=categories)


@dataclass(frozen=True)
class Profile:
    """"My situation" — `content/profile.yaml`."""

    stage: str
    domain: list[str]


def load_profile(path: Path) -> Profile:
    """Load `profile.yaml`.

    Args:
        path: Path to `content/profile.yaml`.

    Returns:
        The parsed `Profile`.
    """
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return Profile(stage=raw["stage"], domain=list(raw.get("domain", [])))
