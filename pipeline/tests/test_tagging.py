"""Articles get taxonomy keyword slugs as tags, chosen by a model and validated by code."""

from __future__ import annotations

from pathlib import Path

import pytest

from founder_atlas_pipeline.frontmatter import dump, parse
from founder_atlas_pipeline.tagging import TaggingError, keyword_menu, tag_article
from founder_atlas_pipeline.taxonomy import load_taxonomy


class FakeTagger:
    def __init__(self, keywords: list[str]) -> None:
        self.keywords = keywords
        self.prompts: list[str] = []

    def tag(self, prompt: str) -> dict:
        self.prompts.append(prompt)
        return {"keywords": self.keywords}


def _write_article(content_root: Path, source_id: str, tags: list[str]) -> Path:
    path = content_root / "source_articles" / f"{source_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    frontmatter = {
        "source": source_id,
        "title_ko": "첫 10명의 고객을 확보하는 법",
        "tldr": "첫 고객은 직접 찾아가 설득한다.",
        "lead": "창업자가 직접 판다.",
        "tags": tags,
        "source_sha256": "0" * 64,
        "generated_at": "2026-09-25",
    }
    path.write_text(dump(frontmatter, "## 1. 직접 찾아가라\n\n지인부터 시작한다."), encoding="utf-8")
    return path


def test_keyword_menu_lists_every_keyword_under_its_category(content_root: Path) -> None:
    menu = keyword_menu(load_taxonomy(content_root / "taxonomy.yaml"))

    assert "고객·세일즈" in menu
    assert "first-customers: 첫 고객 확보" in menu
    assert menu.count("\n- ") >= 40 - 8


def test_tag_article_writes_valid_keyword_slugs_in_model_order(content_root: Path) -> None:
    path = _write_article(content_root, "yc-first-10", ["고객"])
    tagger = FakeTagger(["first-customers", "founder-led-sales", "made-up", "first-customers"])

    result = tag_article(content_root, "yc-first-10", load_taxonomy(content_root / "taxonomy.yaml"), tagger)

    assert result.status == "tagged"
    assert result.tags == ["first-customers", "founder-led-sales"]
    written = parse(path.read_text(encoding="utf-8"))
    assert written.frontmatter["tags"] == ["first-customers", "founder-led-sales"]
    assert written.frontmatter["title_ko"] == "첫 10명의 고객을 확보하는 법"
    assert written.body.startswith("## 1. 직접 찾아가라")
    assert "첫 10명의 고객을 확보하는 법" in tagger.prompts[0]
    assert "지인부터 시작한다." in tagger.prompts[0]


def test_tag_article_keeps_at_most_four_tags(content_root: Path) -> None:
    _write_article(content_root, "many", [])
    tagger = FakeTagger(["first-customers", "pitch", "pivot", "moat", "retention"])

    result = tag_article(content_root, "many", load_taxonomy(content_root / "taxonomy.yaml"), tagger)

    assert result.tags == ["first-customers", "pitch", "pivot", "moat"]


def test_tag_article_skips_articles_already_tagged_with_keywords(content_root: Path) -> None:
    _write_article(content_root, "done", ["pitch"])
    tagger = FakeTagger(["seed-round"])
    taxonomy = load_taxonomy(content_root / "taxonomy.yaml")

    assert tag_article(content_root, "done", taxonomy, tagger).status == "skipped"
    assert tagger.prompts == []
    assert tag_article(content_root, "done", taxonomy, tagger, force=True).tags == ["seed-round"]


def test_tag_article_rejects_answers_with_no_known_keyword(content_root: Path) -> None:
    path = _write_article(content_root, "bad", ["고객"])
    before = path.read_text(encoding="utf-8")

    with pytest.raises(TaggingError):
        tag_article(content_root, "bad", load_taxonomy(content_root / "taxonomy.yaml"), FakeTagger(["고객"]))

    assert path.read_text(encoding="utf-8") == before
