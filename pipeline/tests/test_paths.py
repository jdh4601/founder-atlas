"""Tests for repo-root discovery."""

from __future__ import annotations

from pathlib import Path

import pytest

from founder_atlas_pipeline.paths import RepoRootNotFoundError, content_root, find_repo_root


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "content").mkdir(parents=True)
    (repo / "content" / "taxonomy.yaml").write_text("categories: []\n", encoding="utf-8")
    (repo / "pipeline").mkdir()
    return repo


def test_find_repo_root_from_repo_root(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    assert find_repo_root(repo) == repo


def test_find_repo_root_from_nested_directory(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    nested = repo / "pipeline" / "src" / "founder_atlas_pipeline"
    nested.mkdir(parents=True)
    assert find_repo_root(nested) == repo


def test_find_repo_root_raises_when_absent(tmp_path: Path) -> None:
    isolated = tmp_path / "no-repo-here"
    isolated.mkdir()
    with pytest.raises(RepoRootNotFoundError):
        find_repo_root(isolated)


def test_content_root_returns_content_subdir(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    assert content_root(repo) == repo / "content"
