"""Figures found by web image search, for sources whose original has no images.

A model picks the paragraphs worth illustrating and an English search query
for each, then ranks the returned candidates by their title and page.
Candidates are downloaded in rank order (remote hotlinks break often) and a
vision-capable model looks at each one: the first it judges relevant is kept,
with a caption written from what the image actually shows. Captions credit
the domain of the page the image came from.
"""

from __future__ import annotations

import html
import json
import re
import subprocess
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from urllib.parse import urlparse

import requests

from founder_atlas_pipeline.cli_providers import run_structured_cli
from founder_atlas_pipeline.figures import Figure, FigurePlanner, numbered_paragraphs

_BING_ITEM = re.compile(r'class="iusc"[^>]*?\sm="([^"]+)"')
_BLOCKED_HOSTS = ("licdn.com", "linkedin.com", "fbsbx.com", "facebook.com", "instagram.com", "pinimg.com", "pinterest.")
_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126 Safari/537.36"
)
MAX_CANDIDATES = 8

PICK_SYSTEM_PROMPT = """당신은 스타트업 에세이의 한국어 번역 글에 참고 그림을 넣는 편집자입니다.
번호가 붙은 한국어 문단이 주어집니다. 그림이 이해를 도울 문단을 글 전체에 고르게 고르고,
각 문단의 내용을 설명하는 이미지를 찾을 영어 이미지 검색어를 쓰세요.
검색어는 문단에 나온 구체적인 인물·회사·제품·개념·도식을 가리키게 쓰세요(예: "Airbnb founders 2009", "startup growth hockey stick chart").
caption은 그림이 이 문단에서 무엇을 보여 주는지 한국어 한 문장으로, alt는 짧은 한국어 구로 쓰세요."""

CHOOSE_SYSTEM_PROMPT = """당신은 이미지 검색 결과에서 글 내용과 가장 관련 있는 그림을 고르는 편집자입니다.
각 그림 요청마다 후보의 제목과 출처 페이지를 보고, 문단 내용을 직접 설명할 가능성이 높은 순서로
후보 번호를 최대 4개 나열하세요. 광고, 상품 판매 페이지, 무관한 인물 사진은 빼세요.
적합한 후보가 없으면 빈 목록을 주세요."""

REVIEW_SYSTEM_PROMPT = """첨부한 그림이 아래 한국어 문단의 내용을 이해하는 데 실제로 도움이 되는지 판단하세요.
문단 주제와 직접 관련된 도식·차트·사진이면 relevant를 true로, 무관하거나 광고·로고·
글자가 깨진 저해상도 이미지·워터마크가 큰 이미지이면 false로 하세요.
relevant가 true이면 caption에 그림이 실제로 보여 주는 내용을 문단과 연결해 한국어 1~2문장으로 쓰세요.
그림에 없는 수치나 사실을 쓰지 마세요. alt는 그림을 짧게 설명하는 한국어 구로 쓰세요."""

PICK_SCHEMA = {
    "type": "object",
    "properties": {
        "figures": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "paragraph": {"type": "integer"},
                    "query": {"type": "string"},
                    "alt": {"type": "string"},
                    "caption": {"type": "string"},
                },
                "required": ["paragraph", "query", "alt", "caption"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["figures"],
    "additionalProperties": False,
}
CHOOSE_SCHEMA = {
    "type": "object",
    "properties": {
        "choices": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "figure": {"type": "integer"},
                    "candidates": {"type": "array", "items": {"type": "integer"}},
                },
                "required": ["figure", "candidates"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["choices"],
    "additionalProperties": False,
}


REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "relevant": {"type": "boolean"},
        "alt": {"type": "string"},
        "caption": {"type": "string"},
    },
    "required": ["relevant", "alt", "caption"],
    "additionalProperties": False,
}
MAX_TRIES_PER_FIGURE = 3


class ImageReviewer(Protocol):
    def review(self, paragraph: str, image: Path) -> dict: ...


class CLIImageReviewer:
    """Looks at a downloaded image with a local model CLI that can read images."""

    def __init__(self, provider: str) -> None:
        self.provider = provider

    def review(self, paragraph: str, image: Path) -> dict:
        return run_structured_cli(
            self.provider,
            system_prompt=REVIEW_SYSTEM_PROMPT,
            user_prompt=f"한국어 문단:\n{paragraph}",
            schema=REVIEW_SCHEMA,
            images=[image],
        )


@dataclass(frozen=True)
class ImageCandidate:
    image_url: str
    page_url: str
    title: str


def _is_allowed(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return url.startswith(("http://", "https://")) and not any(blocked in host for blocked in _BLOCKED_HOSTS)


def parse_bing_results(page: str) -> list[ImageCandidate]:
    """Image candidates from a Bing image results page, minus social-network hosts and duplicates."""
    candidates: list[ImageCandidate] = []
    seen: set[str] = set()
    for raw in _BING_ITEM.findall(page):
        try:
            data = json.loads(html.unescape(raw))
        except json.JSONDecodeError:
            continue
        image_url, page_url = data.get("murl", ""), data.get("purl", "")
        if image_url in seen or not _is_allowed(image_url) or not _is_allowed(page_url):
            continue
        seen.add(image_url)
        candidates.append(ImageCandidate(image_url, page_url, data.get("t", "").strip()))
    return candidates


def search_bing_images(query: str) -> list[ImageCandidate]:
    response = requests.get(
        "https://www.bing.com/images/search",
        params={"q": query, "form": "HDRSC2", "first": "1"},
        headers={"User-Agent": _USER_AGENT, "Accept-Language": "en-US"},
        timeout=30,
    )
    response.raise_for_status()
    return parse_bing_results(response.text)[:MAX_CANDIDATES]


def download_image(url: str, output: Path) -> bool:
    """Download an image and re-encode it as a JPEG at most 1200px wide; False if it is not an image."""
    try:
        response = requests.get(url, headers={"User-Agent": _USER_AGENT}, timeout=30)
        response.raise_for_status()
    except requests.RequestException:
        return False
    if not response.headers.get("content-type", "").startswith("image/") or len(response.content) < 5000:
        return False
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=Path(urlparse(url).path).suffix or ".img") as raw:
        raw.write(response.content)
        raw.flush()
        result = subprocess.run(
            ["ffmpeg", "-loglevel", "error", "-y", "-i", raw.name, "-vf", "scale='min(1200,iw)':-2",
             "-frames:v", "1", "-q:v", "4", str(output)],
            capture_output=True, timeout=60,
        )
    return result.returncode == 0 and output.is_file() and output.stat().st_size > 0


def _domain(url: str) -> str:
    host = urlparse(url).netloc.lower()
    return host.removeprefix("www.")


def plan_search_figures(
    body: str,
    source_id: str,
    planner: FigurePlanner,
    reviewer: ImageReviewer,
    *,
    search: Callable[[str], list[ImageCandidate]],
    download: Callable[[str, Path], bool],
    public_dir: Path,
    count: int,
    chooser: FigurePlanner | None = None,
) -> list[Figure]:
    """Find, rank, download, and visually review up to `count` images for the article."""
    paragraphs = numbered_paragraphs(body)
    listing = "\n\n".join(f"[{index}] {text}" for index, text in enumerate(paragraphs, 1))
    picked = planner.plan(f"문단을 {count}개 고르세요.\n\n한국어 문단:\n{listing}").get("figures", [])
    wanted = [
        item for item in picked
        if isinstance(item.get("paragraph"), int) and 1 <= item["paragraph"] <= len(paragraphs)
    ][:count]
    candidates = [search(item["query"]) for item in wanted]

    blocks = []
    for index, (item, found) in enumerate(zip(wanted, candidates, strict=True)):
        options = "\n".join(
            f"  ({number}) 제목: {c.title} / 페이지: {c.page_url}" for number, c in enumerate(found)
        )
        blocks.append(f"[그림 {index}] 문단: {paragraphs[item['paragraph'] - 1]}\n검색어: {item['query']}\n{options}")
    choices = (chooser or planner).plan("\n\n".join(blocks)).get("choices", [])

    figures: list[Figure] = []
    for choice in choices:
        index = choice.get("figure")
        if not isinstance(index, int) or not 0 <= index < len(wanted):
            continue
        ranked = [n for n in choice.get("candidates", []) if isinstance(n, int) and 0 <= n < len(candidates[index])]
        paragraph_number = wanted[index]["paragraph"]
        output = public_dir / "figures" / source_id / f"web-{len(figures) + 1}.jpg"
        for number in ranked[:MAX_TRIES_PER_FIGURE]:
            candidate = candidates[index][number]
            if not download(candidate.image_url, output):
                continue
            verdict = reviewer.review(paragraphs[paragraph_number - 1], output)
            if not verdict.get("relevant"):
                continue
            figures.append(
                Figure(
                    after_paragraph=paragraph_number,
                    src=f"/figures/{source_id}/{output.name}",
                    alt=verdict["alt"].strip(),
                    caption=f"{verdict['caption'].strip()} 출처: {_domain(candidate.page_url)}",
                )
            )
            break
        else:
            output.unlink(missing_ok=True)
    return figures
