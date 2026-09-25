"""Keyword page writers backed by Anthropic API or an authenticated local CLI.

`PageWriterClient` is a `Protocol` so `build_pages/pipeline.py` can be tested
with a fake implementation. Both real implementations use structured output.
The prompt is built only from advice claim/body/context
(Korean) — never the hidden `quote` field — so the page cannot cite material
it wasn't given.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Protocol

from founder_atlas_pipeline.models import AdviceUnit

PAGE_WRITER_MODEL = "claude-sonnet-5"

_SYSTEM_PROMPT = """\
당신은 스타트업 조언 아카이브의 편집자입니다. 주어진 조언 단위들(주장 + 한국어 설명)을
바탕으로 하나의 키워드 페이지를 자유 형식 한국어로 작성하세요.

규칙:
- 가벼운 말투와 구체적인 사례 중심으로 쓸 것.
- 다른 키워드를 언급할 때는 제공된 "관련 키워드" 목록의 slug만 [[slug]] 형태로 링크할 것.
- 근거로 삼은 조언은 반드시 {{advice:advice_id}} 형태로 표시할 것 (제공된 조언 id만 사용).
- 조언 단위에 없는 내용은 지어내지 말 것 - 주어진 조언 claim/body만 재료로 쓸 것.
- 본문은 핵심 질문에 집중해 한국어 800~1,500자 정도로 간결하게 쓸 것. 소제목은 최대 4개.
- 제공된 조언을 모두 나열하지 말고, 서로 다른 관점을 묶어 가장 유용한 근거만 인용할 것.
- 비교, 흐름, 2x2 같은 구조를 설명할 때만 ```mermaid 코드 블록으로 도식을 추가할 것 (선택 사항).
- summary는 질문 라우팅에 쓰이는 한 줄 요약입니다.
"""


@dataclass(frozen=True)
class PageCandidate:
    """A proposed keyword page, before evidence-marker filtering."""

    title: str
    summary: str
    body_ko: str


class PageWriterClient(Protocol):
    """Anything that can write one keyword page from its advice units."""

    def write_page(
        self,
        *,
        keyword_title: str,
        category_title: str,
        advice_units: list[AdviceUnit],
        related_keywords: dict[str, str],
    ) -> PageCandidate:
        """Propose a keyword page body from its advice units."""
        ...


def _page_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "summary": {"type": "string"},
            "body_ko": {"type": "string"},
        },
        "required": ["title", "summary", "body_ko"],
        "additionalProperties": False,
    }


def _format_advice_material(advice_units: list[AdviceUnit]) -> str:
    lines = []
    for unit in advice_units:
        stage = ", ".join(unit.context.stage) or "전체 단계"
        domain = ", ".join(unit.context.domain) or "전체 업종"
        lines.append(
            f"- id: {unit.id}\n"
            f"  주장: {unit.claim}\n"
            f"  설명: {unit.body_ko}\n"
            f"  상황: {stage} / {domain}\n"
            f"  화자: {unit.speaker or '(미상)'}"
        )
    return "\n".join(lines)


def _page_user_content(
    keyword_title: str,
    category_title: str,
    advice_units: list[AdviceUnit],
    related_keywords: dict[str, str],
) -> str:
    related_lines = "\n".join(f"- {slug}: {title}" for slug, title in related_keywords.items())
    return (
        f"키워드: {keyword_title}\n"
        f"카테고리: {category_title}\n\n"
        f"조언 단위 (id / 주장 / 설명 / 상황 / 화자):\n{_format_advice_material(advice_units)}\n\n"
        f"관련 키워드 (링크 가능한 slug):\n{related_lines}"
    )


class ClaudePageWriterClient:
    """Real `PageWriterClient` backed by the Anthropic Messages API."""

    def __init__(self, api_key: str | None = None, model: str = PAGE_WRITER_MODEL) -> None:
        """Create a client, resolving the API key from the environment if omitted.

        Args:
            api_key: Explicit `ANTHROPIC_API_KEY` override.
            model: Model id to use for page writing.
        """
        import anthropic  # local import: keep this module importable without the SDK for tests

        self._model = model
        self._client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))

    def write_page(
        self,
        *,
        keyword_title: str,
        category_title: str,
        advice_units: list[AdviceUnit],
        related_keywords: dict[str, str],
    ) -> PageCandidate:
        """Call Claude to write one keyword page.

        Args:
            keyword_title: The keyword's Korean title (from taxonomy.yaml).
            category_title: The owning category's Korean title.
            advice_units: The advice units tagged with this keyword.
            related_keywords: Map of other keyword slug -> Korean title,
                usable for `[[slug]]` links.

        Returns:
            The proposed page content.
        """
        user_content = _page_user_content(
            keyword_title, category_title, advice_units, related_keywords
        )
        response = self._client.messages.create(
            model=self._model,
            max_tokens=8000,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
            output_config={"format": {"type": "json_schema", "schema": _page_schema()}},
        )
        text = next(block.text for block in response.content if block.type == "text")
        payload = json.loads(text)
        return PageCandidate(
            title=payload["title"], summary=payload["summary"], body_ko=payload["body_ko"]
        )


class CLIPageWriterClient:
    """Write keyword pages with an authenticated Codex or Claude Code CLI."""

    def __init__(self, provider: str) -> None:
        if provider not in ("codex-cli", "claude-code-cli"):
            raise ValueError(f"Unsupported CLI provider: {provider}")
        self._provider = provider

    def write_page(
        self,
        *,
        keyword_title: str,
        category_title: str,
        advice_units: list[AdviceUnit],
        related_keywords: dict[str, str],
    ) -> PageCandidate:
        from founder_atlas_pipeline.cli_providers import run_structured_cli

        user_content = _page_user_content(
            keyword_title, category_title, advice_units, related_keywords
        )
        payload = run_structured_cli(
            self._provider,
            system_prompt=_SYSTEM_PROMPT,
            user_prompt=user_content,
            schema=_page_schema(),
        )
        return PageCandidate(
            title=payload["title"], summary=payload["summary"], body_ko=payload["body_ko"]
        )


class TemplatePageWriterClient:
    """Produce an evidence-led draft without calling a model.

    This copies the extracted claim and explanation verbatim, so the draft
    never adds an unsupported synthesis. A person must still review it.
    """

    def write_page(
        self,
        *,
        keyword_title: str,
        category_title: str,
        advice_units: list[AdviceUnit],
        related_keywords: dict[str, str],
    ) -> PageCandidate:
        chosen = advice_units[:8]
        paragraphs = [
            f"- **{unit.claim}** — {unit.body_ko} {{{{advice:{unit.id}}}}}"
            for unit in chosen
        ]
        return PageCandidate(
            title=keyword_title,
            summary=f"{keyword_title}에 관한 원문 근거 조언 {len(chosen)}개를 모았습니다.",
            body_ko="\n\n".join(paragraphs),
        )
