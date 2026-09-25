"""Tests for content/advice/ read/write."""

from __future__ import annotations

from pathlib import Path

from founder_atlas_pipeline.advice import (
    advice_exists,
    list_advice_ids,
    list_all_advice,
    read_advice,
    write_advice,
)
from founder_atlas_pipeline.models import AdviceAnchor, AdviceContext, AdviceUnit


def _unit(**overrides) -> AdviceUnit:
    defaults = dict(
        id="yc-youtube-pricing--03",
        source="yc-youtube-pricing",
        category="pricing",
        keywords=["pricing-strategy", "first-customers"],
        context=AdviceContext(stage=["pre-seed", "seed"], domain=["b2b"]),
        speaker="Kevin Hale",
        claim="초기 B2B 제품은 가격을 높게 시작하라",
        quote="Charge more than you think you should.",
        anchor=AdviceAnchor(kind="timestamp", start=750, paragraph=None),
        match_score=96.5,
        body_ko="한국어 본문: 조언 설명 2~4문장.",
    )
    defaults.update(overrides)
    return AdviceUnit(**defaults)


def test_write_then_read_advice_round_trips(content_root: Path) -> None:
    unit = _unit()
    write_advice(content_root, unit)

    assert advice_exists(content_root, unit.id)
    loaded = read_advice(content_root, unit.id)
    assert loaded == unit


def test_paragraph_anchor_round_trips(content_root: Path) -> None:
    unit = _unit(
        id="paul-graham-do-things--01",
        anchor=AdviceAnchor(kind="paragraph", start=None, paragraph=4),
    )
    write_advice(content_root, unit)
    loaded = read_advice(content_root, unit.id)
    assert loaded.anchor.kind == "paragraph"
    assert loaded.anchor.paragraph == 4
    assert loaded.anchor.start is None


def test_list_advice_ids_filters_by_source(content_root: Path) -> None:
    write_advice(content_root, _unit(id="src-a--01", source="src-a"))
    write_advice(content_root, _unit(id="src-a--02", source="src-a"))
    write_advice(content_root, _unit(id="src-b--01", source="src-b"))

    assert list_advice_ids(content_root, "src-a") == ["src-a--01", "src-a--02"]
    assert list_advice_ids(content_root) == ["src-a--01", "src-a--02", "src-b--01"]


def test_list_all_advice_reads_every_unit(content_root: Path) -> None:
    write_advice(content_root, _unit(id="src-a--01", source="src-a"))
    write_advice(content_root, _unit(id="src-b--01", source="src-b"))

    units = list_all_advice(content_root)
    assert {u.id for u in units} == {"src-a--01", "src-b--01"}


def test_quote_field_is_persisted_but_never_derived_elsewhere(content_root: Path) -> None:
    """`quote` is internal-only per CLAUDE.md; this only checks it round-trips faithfully."""
    unit = _unit(quote="Verbatim English quote with 'punctuation.'")
    write_advice(content_root, unit)
    loaded = read_advice(content_root, unit.id)
    assert loaded.quote == unit.quote
