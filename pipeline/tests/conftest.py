"""Shared pytest fixtures for the founder_atlas_pipeline test suite."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"
REAL_TAXONOMY = Path(__file__).parent.parent.parent / "content" / "taxonomy.yaml"


@pytest.fixture
def content_root(tmp_path: Path) -> Path:
    """A throwaway `content/` directory seeded with the real taxonomy.yaml.

    Tests get a real, hand-authored taxonomy (8 categories, 5 keywords each)
    without touching the actual repo's `content/`.
    """
    root = tmp_path / "content"
    for sub in ("sources", "advice", "keywords", "questions"):
        (root / sub).mkdir(parents=True)
    shutil.copy(REAL_TAXONOMY, root / "taxonomy.yaml")
    (root / "profile.yaml").write_text(
        "stage: pre-seed\ndomain: [ai, b2b]\n", encoding="utf-8"
    )
    return root
