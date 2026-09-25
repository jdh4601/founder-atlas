"""Tests for content/keywords/ read/write."""

from __future__ import annotations

from pathlib import Path

from founder_atlas_pipeline.keywords import (
    keyword_exists,
    list_keyword_slugs,
    read_keyword,
    write_keyword,
)
from founder_atlas_pipeline.models import KeywordImage, KeywordPage


def _page(**overrides) -> KeywordPage:
    defaults = dict(
        slug="pricing-strategy",
        title="가격 책정",
        category="pricing",
        summary="가격을 정하는 법에 대한 조언 모음",
        reviewed=False,
        advice=["yc-youtube-pricing--01", "yc-youtube-pricing--02"],
        images=[
            KeywordImage(
                src="https://i.ytimg.com/vi/abc/hqdefault.jpg",
                alt="thumbnail",
                source="yc-youtube-pricing",
            )
        ],
        updated_at="2026-09-25",
        body_ko="자유 형식의 한국어 본문.\n{{advice:yc-youtube-pricing--01}}",
    )
    defaults.update(overrides)
    return KeywordPage(**defaults)


def test_write_then_read_keyword_round_trips(content_root: Path) -> None:
    page = _page()
    write_keyword(content_root, page)

    assert keyword_exists(content_root, page.slug)
    loaded = read_keyword(content_root, page.slug)
    assert loaded == page


def test_list_keyword_slugs(content_root: Path) -> None:
    write_keyword(content_root, _page(slug="pricing-strategy"))
    write_keyword(content_root, _page(slug="unit-economics"))
    assert list_keyword_slugs(content_root) == ["pricing-strategy", "unit-economics"]


def test_reviewed_flag_round_trips(content_root: Path) -> None:
    page = _page(reviewed=True)
    write_keyword(content_root, page)
    loaded = read_keyword(content_root, page.slug)
    assert loaded.reviewed is True
