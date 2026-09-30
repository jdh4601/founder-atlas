"""Source articles are grounded in stored raw text and safe to resume."""

from __future__ import annotations

from pathlib import Path

import pytest

from founder_atlas_pipeline.frontmatter import parse
from founder_atlas_pipeline.models import SourceMeta, Transcript
from founder_atlas_pipeline.source_articles import generate_article
from founder_atlas_pipeline.source_tldrs import write_tldr_batch
from founder_atlas_pipeline.sources import write_source


class FakeWriter:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def write(self, prompt: str) -> dict:
        self.prompts.append(prompt)
        return {
            "title_ko": "첫 고객을 찾는 법",
            "tldr": "첫 고객은 직접 만나며 문제를 듣는 과정에서 찾는다.",
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
    assert article.frontmatter["tldr"] == "첫 고객은 직접 만나며 문제를 듣는 과정에서 찾는다."
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
            return {"title_ko": "예시", "tldr": "짧은 원문을 한국어로 요약한 문장입니다.", "lead": "소개", "sections": [{"heading": "짧음", "paragraphs": ["짧음"]}]}

    with pytest.raises(ValueError, match="too short"):
        generate_article(tmp_path, source.id, ShortWriter())
    assert not (tmp_path / "source_articles" / f"{source.id}.md").exists()


def test_backfill_tldr_preserves_body_and_removes_review_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    article_path = tmp_path / "example.md"
    article_path.write_text(
        "---\nsource: example\ntitle_ko: 가격 책정\nlead: 고객이 이해하는 단위로 가격을 매긴다.\n"
        "source_sha256: abc\ngenerated_at: '2026-09-27'\nreviewed: false\n---\n"
        "## 핵심\n\n토큰보다 완료된 작업에 가격을 매긴다.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "founder_atlas_pipeline.source_tldrs.run_structured_cli",
        lambda *args, **kwargs: {
            "items": [{"source": "example", "tldr": "고객이 이해하고 예측할 수 있는 작업 단위로 가격을 매겨야 한다."}]
        },
    )

    assert write_tldr_batch([article_path], "codex-cli") == ["example"]
    article = parse(article_path.read_text(encoding="utf-8"))
    assert article.frontmatter["tldr"].startswith("고객이 이해하고")
    assert "reviewed" not in article.frontmatter
    assert "## 핵심" in article.body


def test_generate_article_never_rewrites_an_insights_article(tmp_path: Path) -> None:
    # Insight articles come from Obsidian notes and hold a hash of the note, not
    # of the transcript, so a fingerprint check would wrongly regenerate them.
    (tmp_path / "sources").mkdir()
    source = SourceMeta(
        id="insights-001",
        title="노트",
        title_ko="",
        url="",
        origin="insights",
        format="blog",
        youtube_id=None,
        published=None,
        speakers=[],
        thumbnail=None,
        images=[],
        ingested_at="2026-09-28",
        summary_ko="",
    )
    write_source(tmp_path, source, Transcript(kind="paragraphs", paragraphs=["노트 본문 " * 400]))
    article = tmp_path / "source_articles" / "insights-001.md"
    article.parent.mkdir()
    article.write_text("---\nsource: insights-001\ntldr: x\nsource_sha256: notthetranscripthash\n---\n본문\n", encoding="utf-8")
    writer = FakeWriter()

    result = generate_article(tmp_path, source.id, writer)

    assert result.status == "skipped"
    assert writer.prompts == []
    assert article.read_text(encoding="utf-8").endswith("본문\n")
