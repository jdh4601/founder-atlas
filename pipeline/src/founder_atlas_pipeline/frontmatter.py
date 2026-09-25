"""YAML frontmatter read/write for `content/**/*.md` files.

Serialization preserves key insertion order (`sort_keys=False`) so the
written YAML matches the field order documented in `docs/content-schema.md`
byte-for-byte in structure, which the web app's parser relies on.
"""

from __future__ import annotations

from dataclasses import dataclass

import yaml

_DELIMITER = "---"


class FrontmatterError(Exception):
    """Raised when a Markdown file does not have valid `--- ... ---` frontmatter."""


@dataclass(frozen=True)
class ParsedMarkdown:
    """A Markdown file split into its frontmatter dict and body text."""

    frontmatter: dict
    body: str


def dump(frontmatter: dict, body: str) -> str:
    """Serialize a frontmatter dict + Markdown body into file contents.

    Args:
        frontmatter: Ordered mapping of frontmatter fields. Order is preserved.
        body: Markdown body text, written after the closing `---`.

    Returns:
        The full file contents, ready to write to disk.
    """
    yaml_text = yaml.safe_dump(
        frontmatter,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )
    body_text = body if body.endswith("\n") else f"{body}\n"
    return f"{_DELIMITER}\n{yaml_text}{_DELIMITER}\n{body_text}"


def parse(text: str) -> ParsedMarkdown:
    """Parse a Markdown file's `--- ... ---` frontmatter and body.

    Args:
        text: Full file contents.

    Returns:
        The parsed frontmatter dict and body text.

    Raises:
        FrontmatterError: If the file does not start with a frontmatter block.
    """
    if not text.startswith(_DELIMITER):
        raise FrontmatterError("Markdown file does not start with '---' frontmatter")
    remainder = text[len(_DELIMITER) :]
    try:
        end_index = remainder.index(f"\n{_DELIMITER}")
    except ValueError as exc:
        raise FrontmatterError("Frontmatter block is not closed with '---'") from exc
    yaml_text = remainder[:end_index]
    body = remainder[end_index + len(f"\n{_DELIMITER}") :]
    data = yaml.safe_load(yaml_text) or {}
    if not isinstance(data, dict):
        raise FrontmatterError("Frontmatter did not parse to a mapping")
    return ParsedMarkdown(frontmatter=data, body=body.lstrip("\n"))
