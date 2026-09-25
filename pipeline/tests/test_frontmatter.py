"""Tests for YAML frontmatter serialization matching the content schema."""

from __future__ import annotations

import pytest

from founder_atlas_pipeline.frontmatter import FrontmatterError, dump, parse


def test_dump_preserves_key_order() -> None:
    fm = {"id": "abc", "title": "Hello", "url": "https://example.com"}
    text = dump(fm, "본문입니다.\n")
    yaml_block = text.split("---\n")[1]
    assert list(yaml_block.splitlines()) == [
        "id: abc",
        "title: Hello",
        "url: https://example.com",
    ]


def test_dump_writes_unicode_unescaped() -> None:
    text = dump({"claim": "가격을 높게 시작하라"}, "한국어 본문")
    assert "가격을 높게 시작하라" in text
    assert "\\u" not in text


def test_dump_ensures_body_has_trailing_newline() -> None:
    text = dump({"a": 1}, "no trailing newline")
    assert text.endswith("no trailing newline\n")


def test_round_trip_dump_then_parse() -> None:
    fm = {"id": "abc", "keywords": ["pricing", "unit-economics"], "match_score": 96.5}
    body = "한국어 본문: 조언 설명.\n"
    text = dump(fm, body)
    parsed = parse(text)
    assert parsed.frontmatter == fm
    assert parsed.body == body


def test_parse_rejects_missing_leading_delimiter() -> None:
    with pytest.raises(FrontmatterError):
        parse("title: no delimiter\nbody text")


def test_parse_rejects_unclosed_frontmatter() -> None:
    with pytest.raises(FrontmatterError):
        parse("---\ntitle: x\nbody with no closing delimiter")


def test_parse_handles_null_values() -> None:
    text = dump({"published": None, "thumbnail": None}, "body")
    parsed = parse(text)
    assert parsed.frontmatter == {"published": None, "thumbnail": None}
