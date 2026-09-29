"""Obsidian insight notes become sources + Korean articles without personal sections."""

from __future__ import annotations

from pathlib import Path

import pytest

from founder_atlas_pipeline.frontmatter import parse
from founder_atlas_pipeline.insights import (
    clean_note_body,
    find_source_url,
    import_insight_note,
    insight_source_id,
    youtube_id_from_url,
)
from founder_atlas_pipeline.models import TranscriptSegment
from founder_atlas_pipeline.sources import read_source, read_transcript

NOTE = """---
title: "유니브 권소영 인터뷰 - IP가 쌓이는 사업"
source: "[[Clippings/런웨이 4개월]]"
original: "https://www.youtube.com/watch?v=tlUjoWhzUz0&t=671s"
speaker: 권소영 (유니브 CEO)
created: 2026-09-28
tags:
  - startup
  - talent
  - pricing
---

## 1. 이미 돈이 되는 사업이 먼저다

- 런웨이는 4개월이었다. [[049_Alex Hormozi Scale or Fail|호르모지]]도 같은 말을 한다.

> 새길 문장: 죽어가는 회사에는 독창성보다 현금 흐름이 먼저다.

## 2. 무료 관행에 가격을 붙여라

- 입시설명회를 5만 원에 팔았다.

---

## 왜 이 인터뷰가 지금 나에게 유효한가

- D.ONE 멤버 질문 로그를 모아볼 것.

## 연결되는 인사이트

- [[048_인사관]] - 연결

## 지금 당장 적용할 것

- 할 일

## 원문

[[Clippings/런웨이 4개월]]
"""


class FakeWriter:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def write(self, prompt: str) -> dict:
        self.prompts.append(prompt)
        return {
            "title_ko": "매출보다 IP가 쌓이는 사업을 남겨라",
            "tldr": "매출 규모보다 회사에 자산이 쌓이는 사업을 골라야 한다.",
            "lead": "런웨이 4개월의 적자 스타트업을 살린 결정들을 정리했다.",
            "tags": ["채용", "가격", "없는태그"],
        }


class FakeYouTube:
    def fetch_segments(self, video_id: str) -> list[TranscriptSegment]:
        return [TranscriptSegment(start=1.0, duration=2.0, text="런웨이가 4개월 남았을 때")]


def test_clean_note_body_drops_personal_sections_and_wikilinks() -> None:
    body = clean_note_body(parse(NOTE).body)

    assert body.startswith("## 1. 이미 돈이 되는 사업이 먼저다")
    assert "호르모지도 같은 말을 한다" in body
    assert "> 새길 문장: 죽어가는 회사에는" in body
    assert body.rstrip().endswith("- 입시설명회를 5만 원에 팔았다.")
    for removed in ("유효한가", "D.ONE", "연결되는 인사이트", "적용할 것", "[[", "Clippings", "---"):
        assert removed not in body


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://www.youtube.com/watch?v=tlUjoWhzUz0&t=671s", "tlUjoWhzUz0"),
        ("https://youtu.be/GucTd0nQKp0?si=abc", "GucTd0nQKp0"),
        ("https://maily.so/post", None),
    ],
)
def test_youtube_id_from_url(url: str, expected: str | None) -> None:
    assert youtube_id_from_url(url) == expected


def test_find_source_url_prefers_original_then_source_then_clipping_then_body(tmp_path: Path) -> None:
    (tmp_path / "Clippings").mkdir()
    (tmp_path / "Clippings" / "Talk.md").write_text(
        '---\nsource: "https://www.youtube.com/watch?v=AAAAAAAAAAA"\n---\n', encoding="utf-8"
    )
    assert find_source_url({"original": "https://x.com/a"}, "", tmp_path) == "https://x.com/a"
    assert find_source_url({"source": "https://youtu.be/BBBBBBBBBBB"}, "", tmp_path) == "https://youtu.be/BBBBBBBBBBB"
    assert (
        find_source_url({"source": "[[Clippings/Talk.md]]"}, "", tmp_path)
        == "https://www.youtube.com/watch?v=AAAAAAAAAAA"
    )
    assert (
        find_source_url({}, "see https://www.youtube.com/watch?v=CCCCCCCCCCC here", tmp_path)
        == "https://www.youtube.com/watch?v=CCCCCCCCCCC"
    )
    assert find_source_url({}, "no link", tmp_path) is None


def test_insight_source_id_uses_note_number_and_dedupes() -> None:
    taken: set[str] = set()
    assert insight_source_id("055_유니브.md", taken) == "insights-055"
    taken.add("insights-035")
    assert insight_source_id("035_Gaurav 두번째.md", taken) == "insights-035-2"


def test_import_insight_note_writes_source_transcript_and_article(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    (vault / "07_Insights").mkdir(parents=True)
    note = vault / "07_Insights" / "055_유니브 권소영 인터뷰.md"
    note.write_text(NOTE, encoding="utf-8")
    content = tmp_path / "content"
    (content / "sources").mkdir(parents=True)
    writer = FakeWriter()

    result = import_insight_note(
        content, vault, note, writer, youtube=FakeYouTube(), thumbnail_for=lambda vid: f"https://i/{vid}.jpg"
    )

    assert result.source_id == "insights-055"
    assert result.status == "written"
    source = read_source(content, "insights-055")
    assert source.origin == "insights"
    assert source.format == "video"
    assert source.youtube_id == "tlUjoWhzUz0"
    assert source.thumbnail == "https://i/tlUjoWhzUz0.jpg"
    assert source.speakers == ["권소영 (유니브 CEO)"]
    assert read_transcript(content, "insights-055").segments[0].text == "런웨이가 4개월 남았을 때"
    article = parse((content / "source_articles" / "insights-055.md").read_text(encoding="utf-8"))
    assert article.frontmatter["title_ko"] == "매출보다 IP가 쌓이는 사업을 남겨라"
    assert article.frontmatter["tags"] == ["채용", "가격"]
    assert "D.ONE" not in article.body and "D.ONE" not in writer.prompts[0]

    again = import_insight_note(
        content, vault, note, writer, youtube=FakeYouTube(), thumbnail_for=lambda vid: None
    )
    assert again.status == "skipped"
    assert len(writer.prompts) == 1


def test_clean_note_body_keeps_numbered_sections_that_mention_to_dos() -> None:
    body = "## 3. 창업자가 해야 할 것은 판매다\n\n- 직접 판다.\n\n## 지금 당장 할 것\n\n- 개인 할 일"
    assert clean_note_body(body) == "## 3. 창업자가 해야 할 것은 판매다\n\n- 직접 판다."


def test_import_insight_note_retries_when_only_the_source_was_written(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    (vault / "07_Insights").mkdir(parents=True)
    note = vault / "07_Insights" / "055_note.md"
    note.write_text(NOTE, encoding="utf-8")
    content = tmp_path / "content"
    (content / "sources").mkdir(parents=True)

    class FailingWriter:
        def write(self, prompt: str) -> dict:
            raise RuntimeError("session limit reached")

    with pytest.raises(RuntimeError):
        import_insight_note(content, vault, note, FailingWriter(), youtube=FakeYouTube(), thumbnail_for=lambda v: None)

    result = import_insight_note(content, vault, note, FakeWriter(), youtube=FakeYouTube(), thumbnail_for=lambda v: None)
    assert result.status == "written"


def test_import_insight_note_accepts_notes_without_frontmatter(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    (vault / "07_Insights").mkdir(parents=True)
    note = vault / "07_Insights" / "036_조직 AX의 진짜 의미.md"
    note.write_text("단순 업무에 AI를 도입하는 것이 아니다.\n\n## 핵심\n\n- 워크플로우를 다시 설계한다.\n", encoding="utf-8")
    content = tmp_path / "content"
    (content / "sources").mkdir(parents=True)

    result = import_insight_note(content, vault, note, FakeWriter(), youtube=FakeYouTube(), thumbnail_for=lambda v: None)

    source = read_source(content, result.source_id)
    assert source.title == "조직 AX의 진짜 의미"
    assert source.format == "blog" and source.url == ""
    article = parse((content / "source_articles" / f"{result.source_id}.md").read_text(encoding="utf-8"))
    assert article.body.startswith("단순 업무에 AI를 도입하는 것이 아니다.")
