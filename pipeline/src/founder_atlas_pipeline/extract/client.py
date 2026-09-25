"""Claude-backed advice extraction client.

`ExtractClient` is a `Protocol` so `extract/pipeline.py` can be tested with a
fake implementation that never touches the network. `ClaudeExtractClient` is
the real implementation, built per `claude-api` skill guidance: structured
output via `output_config.format` (json_schema) on `claude-sonnet-5`.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Protocol

EXTRACTION_MODEL = "claude-sonnet-5"

_SYSTEM_PROMPT = """\
당신은 스타트업 조언 큐레이터입니다. 주어진 원문(영어 인터뷰/에세이 일부)에서
창업자에게 실질적으로 도움이 되는 조언을 0개 이상 추출하세요.

각 조언 후보에 대해:
- claim: 한 줄 한국어 주장 (제목처럼 짧고 명확하게)
- body_ko: 2~4문장 한국어 설명. 가볍고 대화체이며, 원문에 나온 구체적인 사례를 포함할 것.
- quote: 원문에서 그대로 가져온 영어 인용문 (한 글자도 바꾸지 말 것 - 그대로 복사)
- category: 아래 제공된 카테고리 slug 중 정확히 하나
- keywords: 아래 제공된 키워드 slug 중 1~3개
- stage: 이 조언이 특히 유효한 단계 slug 목록 (idea, pre-seed, seed, series-a, growth). 모든 단계에 해당하면 빈 배열.
- domain: 이 조언이 특히 유효한 업종 slug 목록 (ai, b2b, b2c, saas, marketplace, devtools, consumer, hardware). 모든 업종에 해당하면 빈 배열.
- speaker: 이 조언을 말한 사람 이름 (원문에 명시된 화자 목록에서 고를 것, 불명확하면 null)

quote는 반드시 원문에 실제로 등장하는 문자열이어야 합니다 - 나중에 코드가
자동으로 대조 검증하므로, 지어내거나 의역하면 안 됩니다.
"""


@dataclass(frozen=True)
class ExtractionCandidate:
    """One raw advice candidate proposed by the model, before verification."""

    claim: str
    body_ko: str
    quote: str
    category: str
    keywords: list[str] = field(default_factory=list)
    stage: list[str] = field(default_factory=list)
    domain: list[str] = field(default_factory=list)
    speaker: str | None = None


class ExtractClient(Protocol):
    """Anything that can turn a transcript chunk into advice candidates."""

    def extract_candidates(
        self,
        chunk_text: str,
        *,
        source_title: str,
        speakers: list[str],
        category_slugs: list[str],
        keyword_slugs: list[str],
    ) -> list[ExtractionCandidate]:
        """Propose advice candidates found in one transcript chunk."""
        ...


def _candidate_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "candidates": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "claim": {"type": "string"},
                        "body_ko": {"type": "string"},
                        "quote": {"type": "string"},
                        "category": {"type": "string"},
                        "keywords": {"type": "array", "items": {"type": "string"}},
                        "stage": {"type": "array", "items": {"type": "string"}},
                        "domain": {"type": "array", "items": {"type": "string"}},
                        "speaker": {"type": ["string", "null"]},
                    },
                    "required": [
                        "claim",
                        "body_ko",
                        "quote",
                        "category",
                        "keywords",
                        "stage",
                        "domain",
                        "speaker",
                    ],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["candidates"],
        "additionalProperties": False,
    }


class ClaudeExtractClient:
    """Real `ExtractClient` backed by the Anthropic Messages API."""

    def __init__(self, api_key: str | None = None, model: str = EXTRACTION_MODEL) -> None:
        """Create a client, resolving the API key from the environment if omitted.

        Args:
            api_key: Explicit `ANTHROPIC_API_KEY` override. Falls back to the
                `ANTHROPIC_API_KEY` env var (loaded from `.env` by the CLI).
            model: Model id to use for extraction.
        """
        import anthropic  # local import: keep this module importable without the SDK for tests

        self._model = model
        self._client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))

    def extract_candidates(
        self,
        chunk_text: str,
        *,
        source_title: str,
        speakers: list[str],
        category_slugs: list[str],
        keyword_slugs: list[str],
    ) -> list[ExtractionCandidate]:
        """Call Claude to propose advice candidates for one transcript chunk.

        Args:
            chunk_text: The transcript chunk text.
            source_title: The source's original (English) title, for context.
            speakers: Known speaker names for this source.
            category_slugs: Valid category slugs (from taxonomy.yaml).
            keyword_slugs: Valid keyword slugs (from taxonomy.yaml).

        Returns:
            Raw candidates as proposed by the model (not yet verified).
        """
        user_content = (
            f"제목: {source_title}\n"
            f"화자 목록: {', '.join(speakers) or '(명시되지 않음)'}\n"
            f"사용 가능한 카테고리: {', '.join(category_slugs)}\n"
            f"사용 가능한 키워드: {', '.join(keyword_slugs)}\n\n"
            f"원문:\n{chunk_text}"
        )
        response = self._client.messages.create(
            model=self._model,
            max_tokens=8000,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
            output_config={"format": {"type": "json_schema", "schema": _candidate_schema()}},
        )
        text = next(block.text for block in response.content if block.type == "text")
        payload = json.loads(text)
        return [ExtractionCandidate(**c) for c in payload.get("candidates", [])]
