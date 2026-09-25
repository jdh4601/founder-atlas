"""Tests for id/slug generation."""

from __future__ import annotations

import pytest

from founder_atlas_pipeline.slugs import (
    make_advice_id,
    make_source_id,
    next_advice_index,
    slugify,
)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("How to Price Your Product", "how-to-price-your-product"),
        ("Y Combinator: Startup 101!!", "y-combinator-startup-101"),
        ("  leading and trailing  ", "leading-and-trailing"),
        ("Café résumé", "cafe-resume"),
        ("", "untitled"),
        ("!!!", "untitled"),
    ],
)
def test_slugify_produces_lowercase_kebab_ascii(text: str, expected: str) -> None:
    assert slugify(text) == expected


def test_slugify_truncates_to_max_words() -> None:
    long_title = "one two three four five six seven eight nine ten"
    assert slugify(long_title, max_words=3) == "one-two-three"


def test_make_source_id_joins_origin_and_slug() -> None:
    assert (
        make_source_id("yc-youtube", "How to Price Your Product")
        == "yc-youtube-how-to-price-your-product"
    )


def test_make_advice_id_pads_two_digits() -> None:
    assert make_advice_id("yc-youtube-pricing", 3) == "yc-youtube-pricing--03"
    assert make_advice_id("yc-youtube-pricing", 12) == "yc-youtube-pricing--12"


@pytest.mark.parametrize("bad_index", [0, -1, 100])
def test_make_advice_id_rejects_out_of_range_index(bad_index: int) -> None:
    with pytest.raises(ValueError):
        make_advice_id("src", bad_index)


def test_next_advice_index_fills_gaps() -> None:
    assert next_advice_index([]) == 1
    assert next_advice_index(["src--01"]) == 2
    assert next_advice_index(["src--01", "src--03"]) == 2
    assert next_advice_index(["src--01", "src--02"]) == 3
