"""Generate source-grounded Korean reading articles from ingested raw text."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Protocol

from founder_atlas_pipeline.cli_providers import run_structured_cli
from founder_atlas_pipeline.frontmatter import dump, parse
from founder_atlas_pipeline.sources import read_source, source_transcript_path


SYSTEM_PROMPT = """당신은 영어 원문을 한국어로 옮겨 읽기 좋은 스타트업 블로그 글을 쓰는 편집자입니다.
제공된 원문 전체를 읽고 논지와 중요한 사례를 빠뜨리지 않도록 한국어 글로 재구성하세요.
자막의 반복, 구어체 군더더기, 광고만 덜어내고 원문의 주장 순서와 맥락을 지키세요.
제목, 도입, 원문 길이에 맞는 소제목과 문단을 작성하세요.
각 문단은 자연스러운 완결된 한국어 문장으로 쓰고, 핵심 수치·인물·사례를 정확히 옮기세요.
원문에 없는 사례, 인용, 수치, 결론을 추가하지 마세요. 불확실하면 단정하지 마세요.
직역문이나 조언 목록 대신 원문을 읽는 느낌의 에세이·블로그 본문으로 쓰세요.
이미지 URL이나 마크다운 이미지는 생성하지 마세요. 실제 수집된 이미지는 앱에서 별도로 표시합니다.
"""


ARTICLE_SCHEMA = {
    "type": "object",
    "properties": {
        "title_ko": {"type": "string"},
        "lead": {"type": "string"},
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "heading": {"type": "string"},
                    "paragraphs": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["heading", "paragraphs"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["title_ko", "lead", "sections"],
    "additionalProperties": False,
}


class ArticleWriter(Protocol):
    def write(self, prompt: str) -> dict: ...


class CLIArticleWriter:
    def __init__(self, provider: str) -> None:
        self.provider = provider

    def write(self, prompt: str) -> dict:
        return run_structured_cli(
            self.provider,
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
            schema=ARTICLE_SCHEMA,
        )


@dataclass(frozen=True)
class ArticleResult:
    source_id: str
    status: str
    path: Path


def article_path(content_root: Path, source_id: str) -> Path:
    return content_root / "source_articles" / f"{source_id}.md"


def _source_text(payload: dict) -> str:
    if payload.get("kind") == "segments":
        return "\n".join(
            f"[{int(segment['start']) // 60:02d}:{int(segment['start']) % 60:02d}] {segment['text']}"
            for segment in payload["segments"]
        )
    if payload.get("kind") == "paragraphs":
        return "\n\n".join(payload["paragraphs"])
    raise ValueError("Unknown transcript kind")


def _validated_article(data: dict, source_length: int) -> tuple[str, str, str]:
    title = data["title_ko"].strip()
    lead = data["lead"].strip()
    sections = data["sections"]
    minimum_sections = 1 if source_length < 2500 else 2 if source_length < 7000 else 4
    if not title or not lead or not minimum_sections <= len(sections) <= 12:
        raise ValueError(f"Article needs a title, lead, and at least {minimum_sections} sections")
    if not any("가" <= char <= "힣" for char in title + lead):
        raise ValueError("Article title and lead must be in Korean")
    body_parts: list[str] = []
    for section in sections:
        heading = section["heading"].strip()
        paragraphs = [paragraph.strip() for paragraph in section["paragraphs"]]
        if not heading or not paragraphs or any(not paragraph for paragraph in paragraphs):
            raise ValueError("Article section is empty")
        body_parts.append("## " + heading + "\n\n" + "\n\n".join(paragraphs))
    body = "\n\n".join(body_parts)
    minimum_body = max(180, min(1000, source_length // 7))
    if len(body) < minimum_body:
        raise ValueError("Article is too short to cover the source")
    return title, lead, body


def generate_article(
    content_root: Path, source_id: str, writer: ArticleWriter, *, force: bool = False
) -> ArticleResult:
    source = read_source(content_root, source_id)
    transcript_file = source_transcript_path(content_root, source_id)
    raw = transcript_file.read_bytes()
    fingerprint = hashlib.sha256(raw).hexdigest()
    output = article_path(content_root, source_id)
    if output.exists() and not force:
        prior = parse(output.read_text(encoding="utf-8"))
        if prior.frontmatter.get("source_sha256") == fingerprint:
            return ArticleResult(source_id, "skipped", output)
    source_text = _source_text(json.loads(raw))
    if not source_text.strip():
        raise ValueError(f"Source has no raw text: {source_id}")
    section_guidance = "1~2개" if len(source_text) < 2500 else "2~4개" if len(source_text) < 7000 else "4~8개"
    prompt = (
        f"원문 제목: {source.title}\n원문 URL: {source.url}\n"
        f"형식: {source.format}\n화자: {', '.join(source.speakers) or '미상'}\n\n"
        f"원문 길이에 맞게 소제목 {section_guidance}를 쓰세요. 짧은 원문을 억지로 늘리지 마세요.\n\n"
        f"원문 전체:\n{source_text}"
    )
    title, lead, body = _validated_article(writer.write(prompt), len(source_text))
    frontmatter = {
        "source": source_id,
        "title_ko": title,
        "lead": lead,
        "source_sha256": fingerprint,
        "generated_at": date.today().isoformat(),
        "reviewed": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".md.tmp")
    temporary.write_text(dump(frontmatter, body), encoding="utf-8")
    temporary.replace(output)
    return ArticleResult(source_id, "written", output)
