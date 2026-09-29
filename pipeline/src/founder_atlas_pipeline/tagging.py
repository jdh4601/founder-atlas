"""Tag each source article with the taxonomy keywords it actually covers.

Tags are keyword slugs from `content/taxonomy.yaml`, so the home page can
filter contents by the same category keywords the keyword pages use. A model
reads the Korean article and picks keywords; code drops anything that is not
a known slug and caps the count.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from founder_atlas_pipeline.cli_providers import run_structured_cli
from founder_atlas_pipeline.frontmatter import dump, parse
from founder_atlas_pipeline.source_articles import article_path
from founder_atlas_pipeline.taxonomy import Taxonomy

MAX_TAGS = 4
MAX_BODY_CHARS = 8000

SYSTEM_PROMPT = """당신은 창업가를 위한 콘텐츠 아카이브의 분류 담당자입니다.
아래 한국어 글이 실제로 다루는 주제를 키워드 목록에서 골라 slug로 답하세요.
- 글의 한 섹션 이상을 차지하거나 핵심 주장과 직접 연결된 키워드만 고르세요. 스치듯 언급한 주제는 고르지 마세요.
- 넓은 주제보다 구체적인 키워드를 고르세요. 예: 첫 고객을 찾는 방법이 핵심이면 first-customers.
- 가장 중심이 되는 키워드부터 1~4개를 고르세요.
- 목록에 없는 slug는 쓰지 마세요."""

SCHEMA = {
    "type": "object",
    "properties": {"keywords": {"type": "array", "items": {"type": "string"}}},
    "required": ["keywords"],
    "additionalProperties": False,
}


class TaggingError(Exception):
    """The model returned no keyword that exists in the taxonomy."""


class Tagger(Protocol):
    def tag(self, prompt: str) -> dict: ...


class CLITagger:
    def __init__(self, provider: str) -> None:
        self.provider = provider

    def tag(self, prompt: str) -> dict:
        return run_structured_cli(self.provider, system_prompt=SYSTEM_PROMPT, user_prompt=prompt, schema=SCHEMA)


@dataclass(frozen=True)
class TagResult:
    source_id: str
    status: str  # tagged | skipped
    tags: list[str]


def keyword_menu(taxonomy: Taxonomy) -> str:
    """Every keyword as `- slug: title`, grouped under its category title."""
    sections = []
    for category in taxonomy.categories:
        lines = "\n".join(f"- {kw.slug}: {kw.title}" for kw in category.keywords)
        sections.append(f"[{category.title}]\n{lines}")
    return "\n\n".join(sections)


def _valid_tags(answer: dict, known: set[str]) -> list[str]:
    tags: list[str] = []
    for slug in answer.get("keywords", []):
        if slug in known and slug not in tags:
            tags.append(slug)
    return tags[:MAX_TAGS]


def tag_article(
    content_root: Path, source_id: str, taxonomy: Taxonomy, tagger: Tagger, *, force: bool = False
) -> TagResult:
    """Replace `tags` in `source_articles/{id}.md` with model-picked keyword slugs.

    Articles whose tags are already all known keyword slugs are skipped
    unless `force` is set, so old topic words like `고객` get retagged.
    """
    path: Path = article_path(content_root, source_id)
    parsed = parse(path.read_text(encoding="utf-8"))
    known = taxonomy.keyword_slugs()
    current = parsed.frontmatter.get("tags") or []
    if current and all(tag in known for tag in current) and not force:
        return TagResult(source_id, "skipped", list(current))

    fm = parsed.frontmatter
    prompt = (
        f"키워드 목록:\n{keyword_menu(taxonomy)}\n\n"
        f"글 제목: {fm.get('title_ko', '')}\n요약: {fm.get('tldr', '')}\n도입: {fm.get('lead', '')}\n\n"
        f"본문:\n{parsed.body[:MAX_BODY_CHARS]}"
    )
    tags = _valid_tags(tagger.tag(prompt), known)
    if not tags:
        raise TaggingError(f"{source_id}: no known keyword in the model's answer")
    path.write_text(dump({**fm, "tags": tags}, parsed.body), encoding="utf-8")
    return TagResult(source_id, "tagged", tags)
