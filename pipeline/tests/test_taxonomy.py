"""Tests for taxonomy.yaml loading and validation."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from founder_atlas_pipeline.taxonomy import (
    TaxonomyError,
    load_profile,
    load_taxonomy,
)


def _write_taxonomy(path: Path, categories: list[dict]) -> Path:
    path.write_text(yaml.safe_dump({"categories": categories}), encoding="utf-8")
    return path


def _category(slug: str, n_keywords: int) -> dict:
    return {
        "slug": slug,
        "title": slug,
        "color": "#000000",
        "keywords": [{"slug": f"{slug}-kw-{i}", "title": f"kw {i}"} for i in range(n_keywords)],
    }


def test_load_taxonomy_reads_real_file(tmp_path: Path, content_root: Path) -> None:
    taxonomy = load_taxonomy(content_root / "taxonomy.yaml")
    assert len(taxonomy.categories) == 8
    assert "pricing" in taxonomy.category_slugs()
    assert "unit-economics" in taxonomy.keyword_slugs()


def test_load_taxonomy_rejects_wrong_category_count(tmp_path: Path) -> None:
    path = _write_taxonomy(tmp_path / "taxonomy.yaml", [_category("only-one", 1)])
    with pytest.raises(TaxonomyError, match="exactly 8 categories"):
        load_taxonomy(path)


def test_load_taxonomy_rejects_too_many_keywords_in_a_category(tmp_path: Path) -> None:
    categories = [_category(f"cat-{i}", 1) for i in range(7)]
    categories.append(_category("overflowing", 21))
    path = _write_taxonomy(tmp_path / "taxonomy.yaml", categories)
    with pytest.raises(TaxonomyError, match="max is 20"):
        load_taxonomy(path)


def test_load_taxonomy_rejects_duplicate_keyword_slugs_across_categories(
    tmp_path: Path,
) -> None:
    categories = [_category(f"cat-{i}", 1) for i in range(7)]
    dup = _category("dup-cat", 1)
    dup["keywords"][0]["slug"] = "cat-0-kw-0"  # collides with cat-0's keyword
    categories.append(dup)
    path = _write_taxonomy(tmp_path / "taxonomy.yaml", categories)
    with pytest.raises(TaxonomyError, match="globally unique"):
        load_taxonomy(path)


def test_category_for_keyword_and_keywords_for_category(content_root: Path) -> None:
    taxonomy = load_taxonomy(content_root / "taxonomy.yaml")
    category = taxonomy.category_for_keyword("pricing-strategy")
    assert category is not None
    assert category.slug == "pricing"
    assert taxonomy.category_for_keyword("does-not-exist") is None
    assert len(taxonomy.keywords_for_category("pricing")) == 5


def test_load_profile(content_root: Path) -> None:
    profile = load_profile(content_root / "profile.yaml")
    assert profile.stage == "pre-seed"
    assert profile.domain == ["ai", "b2b"]
