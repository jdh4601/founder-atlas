"""Add concise Korean takeaways to existing source articles in batches."""

from __future__ import annotations

import json
import re
from pathlib import Path

from founder_atlas_pipeline.cli_providers import run_structured_cli
from founder_atlas_pipeline.frontmatter import dump, parse


TLDR_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"source": {"type": "string"}, "tldr": {"type": "string"}},
                "required": ["source", "tldr"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["items"],
    "additionalProperties": False,
}


def missing_tldr_paths(content_root: Path) -> list[Path]:
    paths = sorted((content_root / "source_articles").glob("*.md"))
    return [path for path in paths if not parse(path.read_text(encoding="utf-8")).frontmatter.get("tldr")]


def write_tldr_batch(paths: list[Path], provider: str) -> list[str]:
    material = []
    for path in paths:
        article = parse(path.read_text(encoding="utf-8"))
        fm = article.frontmatter
        headings = re.findall(r"^## (.+)$", article.body, flags=re.MULTILINE)
        material.append({
            "source": fm["source"], "title": fm["title_ko"],
            "lead": fm["lead"], "headings": headings,
        })
    response = run_structured_cli(
        provider,
        system_prompt=(
            "당신은 한국어 블로그 편집자입니다. 각 글의 제목, 도입, 소제목을 읽고 "
            "핵심 주장 또는 독자가 얻을 행동 지침을 한 문장으로 요약하세요. "
            "도입 첫 문장을 그대로 복사하지 말고 글 전체를 압축하세요. "
            "원문에 없는 주장이나 수치를 추가하지 마세요. "
            "각 tldr은 한국어 25~120자이며 줄바꿈 없이 하나의 문장이어야 합니다."
        ),
        user_prompt=json.dumps(material, ensure_ascii=False),
        schema=TLDR_SCHEMA,
    )
    items = response["items"]
    expected = {item["source"] for item in material}
    actual = [item["source"] for item in items]
    if len(actual) != len(expected) or set(actual) != expected:
        raise ValueError("TLDR batch returned missing, duplicate, or unknown source IDs")
    tldrs = {item["source"]: item["tldr"].strip() for item in items}
    for source_id, tldr in tldrs.items():
        if not 25 <= len(tldr) <= 140 or "\n" in tldr or not any("가" <= char <= "힣" for char in tldr):
            raise ValueError(f"Invalid Korean TLDR for {source_id}")
    for path in paths:
        article = parse(path.read_text(encoding="utf-8"))
        fm = article.frontmatter
        fm.pop("reviewed", None)
        ordered = {}
        for key, value in fm.items():
            ordered[key] = value
            if key == "title_ko":
                ordered["tldr"] = tldrs[fm["source"]]
        temporary = path.with_suffix(".md.tmp")
        temporary.write_text(dump(ordered, article.body), encoding="utf-8")
        temporary.replace(path)
    return actual
