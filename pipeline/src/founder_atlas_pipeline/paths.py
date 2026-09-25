"""Repo-root and content-directory discovery.

The pipeline is always invoked from somewhere inside the `founder-atlas`
repository (usually `pipeline/`), but writes into `content/` at the repo
root. This module locates that root without hardcoding an absolute path,
so the CLI works the same way regardless of the caller's working directory.
"""

from __future__ import annotations

from pathlib import Path


class RepoRootNotFoundError(Exception):
    """Raised when no ancestor directory contains a `content/taxonomy.yaml` marker."""


def find_repo_root(start: Path | None = None) -> Path:
    """Walk upward from `start` until a directory containing `content/taxonomy.yaml` is found.

    Args:
        start: Directory to start searching from. Defaults to the current
            working directory.

    Returns:
        The repository root directory.

    Raises:
        RepoRootNotFoundError: If no ancestor directory has `content/taxonomy.yaml`.
    """
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "content" / "taxonomy.yaml").is_file():
            return candidate
    raise RepoRootNotFoundError(
        f"Could not find repo root (content/taxonomy.yaml) above {current}"
    )


def content_root(start: Path | None = None) -> Path:
    """Return the `content/` directory of the repo containing `start`.

    Args:
        start: Directory to start searching from. Defaults to the current
            working directory.

    Returns:
        Path to the `content/` directory.
    """
    return find_repo_root(start) / "content"
