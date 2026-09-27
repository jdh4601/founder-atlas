"""Source articles are grounded in stored raw text and safe to resume."""

from __future__ import annotations

from pathlib import Path

import pytest

from founder_atlas_pipeline.frontmatter import parse
from founder_atlas_pipeline.models import SourceMeta, Transcript
from founder_atlas_pipeline.source_articles import generate_article
from founder_atlas_pipeline.sources import write_source


class FakeWriter:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def write(self, prompt: str) -> dict:
        self.prompts.append(prompt)
        return {
            "title_ko": "첫 고객을 찾는 법",
            "lead": "원문을 읽고 정리한 도입 문단입니다.",
            "sections": [
                {"heading": f"장면 {index}", "paragraphs": ["원문에 나온 내용을 한국어로 풀어 쓴 문단입니다. " * 12]}
                for index in range(4)
            ],
        }


def test_generate_article_reads_raw_text_and_skips_unchanged_source(tmp_path: Path) -> None:
    (tmp_path / "sources").mkdir()
    source = SourceMeta(
        id="yc-youtube-first-customers",
        title="First Customers",
        title_ko="",
        url="https://www.youtube.com/watch?v=example",
        origin="yc-youtube",
        format="video",
        youtube_id="example",
        published=None,
        speakers=["Max"],
        thumbnail=None,
        images=[],
        ingested_at="2026-09-25",
        summary_ko="",
    )
    write_source(tmp_path, source, Transcript(kind="paragraphs", paragraphs=["Talk to real customers. " * 400]))
    writer = FakeWriter()

    first = generate_article(tmp_path, source.id, writer)
    second = generate_article(tmp_path, source.id, writer)

    assert first.status == "written"
    assert second.status == "skipped"
    assert len(writer.prompts) == 1
    assert "Talk to real customers." in writer.prompts[0]
    article = parse(first.path.read_text(encoding="utf-8"))
    assert article.frontmatter["source"] == source.id
    assert "## 장면 1" in article.body


def test_rejects_short_article_without_writing(tmp_path: Path) -> None:
    (tmp_path / "sources").mkdir()
    source = SourceMeta(
        id="paul-graham-example",
        title="Example",
        title_ko="",
        url="https://paulgraham.com/example.html",
        origin="paul-graham",
        format="essay",
        published=None,
        speakers=[],
        thumbnail=None,
        images=[],
        ingested_at="2026-09-25",
        summary_ko="",
    )
    write_source(tmp_path, source, Transcript(kind="paragraphs", paragraphs=["Original text."]))

    class ShortWriter:
        def write(self, prompt: str) -> dict:
            return {"title_ko": "예시", "lead": "소개", "sections": [{"heading": "짧음", "paragraphs": ["짧음"]}]}

    with pytest.raises(ValueError, match="too short"):
        generate_article(tmp_path, source.id, ShortWriter())
    assert not (tmp_path / "source_articles" / f"{source.id}.md").exists()
