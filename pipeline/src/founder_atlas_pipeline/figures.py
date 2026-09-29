"""Place figures inside Korean source articles (`content/source_articles/`).

Figures are Markdown images, `![alt](<src> "caption")`, placed after a
numbered body paragraph. Videos get frames captured at a timestamp that code
computes by matching a model-chosen transcript quote (see `verify.py`); the
model never supplies a timestamp. Blog posts get every body image of the
original page, placed by the model next to the paragraph it illustrates.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Protocol

import lxml.html
import requests

from founder_atlas_pipeline.cli_providers import run_structured_cli
from founder_atlas_pipeline.frontmatter import dump, parse
from founder_atlas_pipeline.models import Transcript
from founder_atlas_pipeline.source_articles import article_path
from founder_atlas_pipeline.sources import read_source, read_transcript
from founder_atlas_pipeline.verify import verify_quote_against_transcript

MIN_QUOTE_SCORE = 90
MIN_FRAME_GAP_SECONDS = 15
MIN_FIGURES = 2
_FIGURE_BLOCK = re.compile(r"^!\[[^\]]*\]\(.*\)$", re.DOTALL)
_BLOCK_SPLIT = re.compile(r"\n\s*\n")
_ORIGIN_CREDITS = {"a16z": "a16z", "paul-graham": "Paul Graham", "yc-youtube": "YC", "lightcone": "YC"}

VIDEO_SYSTEM_PROMPT = """당신은 스타트업 영상 요약 글에 영상 장면 캡처를 배치하는 편집자입니다.
번호가 붙은 한국어 문단과 타임스탬프가 달린 영어 자막이 주어집니다.
글의 핵심 주장이나 사례를 담은 문단을 글 전체에 고르게 고르고, 각 문단의 근거가 된 자막 문장을
자막에서 한 글자도 바꾸지 말고 8~25단어로 그대로 복사하세요. 타임스탬프는 쓰지 마세요.
caption은 그 장면에서 화자가 말하는 내용을 한국어 한 문장으로, alt는 장면을 짧게 설명하세요.
자막에 없는 내용을 지어내지 마세요."""

ARTICLE_SYSTEM_PROMPT = """당신은 영어 원문을 한국어로 옮긴 글에 원문 그림을 배치하는 편집자입니다.
번호가 붙은 한국어 문단과, 원문 그림 목록(그림 설명과 그림 바로 앞의 원문 문맥)이 주어집니다.
모든 그림을 그 그림이 설명하는 내용을 담은 한국어 문단 뒤에 배치하세요.
caption은 그림이 보여 주는 내용을 한국어 1~2문장으로 쓰되, 그림 설명과 문맥에 있는 내용만 쓰세요.
alt는 그림을 짧게 설명하는 한국어 구로 쓰세요."""

_FIGURE_ITEM = {
    "paragraph": {"type": "integer"},
    "alt": {"type": "string"},
    "caption": {"type": "string"},
}
VIDEO_SCHEMA = {
    "type": "object",
    "properties": {
        "figures": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {**_FIGURE_ITEM, "quote": {"type": "string"}},
                "required": ["paragraph", "quote", "alt", "caption"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["figures"],
    "additionalProperties": False,
}
ARTICLE_SCHEMA = {
    "type": "object",
    "properties": {
        "figures": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {**_FIGURE_ITEM, "image": {"type": "integer"}},
                "required": ["image", "paragraph", "alt", "caption"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["figures"],
    "additionalProperties": False,
}


class FigurePlanner(Protocol):
    def plan(self, prompt: str) -> dict: ...


class CLIFigurePlanner:
    """Plans figure placement with a local model CLI (Codex or Claude Code)."""

    def __init__(self, provider: str, system_prompt: str, schema: dict) -> None:
        self.provider = provider
        self.system_prompt = system_prompt
        self.schema = schema

    def plan(self, prompt: str) -> dict:
        return run_structured_cli(
            self.provider, system_prompt=self.system_prompt, user_prompt=prompt, schema=self.schema
        )


@dataclass(frozen=True)
class Figure:
    """One image placed after the `after_paragraph`-th (1-based) body paragraph."""

    after_paragraph: int
    src: str
    alt: str
    caption: str


@dataclass(frozen=True)
class PlannedFrame:
    after_paragraph: int
    start: int
    alt: str
    caption: str


@dataclass(frozen=True)
class ArticleImage:
    src: str
    alt: str
    context: str


@dataclass(frozen=True)
class FigureResult:
    source_id: str
    status: str  # written | partial | skipped | no-figures
    count: int


def _blocks(body: str) -> list[str]:
    return [block.strip() for block in _BLOCK_SPLIT.split(body.strip()) if block.strip()]


def _is_figure(block: str) -> bool:
    return bool(_FIGURE_BLOCK.match(block))


def _is_paragraph(block: str) -> bool:
    return not block.startswith("#") and not _is_figure(block)


def numbered_paragraphs(body: str) -> list[str]:
    """Body paragraphs in order, excluding headings and figures (index 0 = paragraph 1)."""
    return [block for block in _blocks(body) if _is_paragraph(block)]


def strip_figures(body: str) -> str:
    return "\n\n".join(block for block in _blocks(body) if not _is_figure(block))


def has_figures(body: str) -> bool:
    return any(_is_figure(block) for block in _blocks(body))


def figure_markdown(figure: Figure) -> str:
    alt = figure.alt.replace("[", "").replace("]", "").strip()
    caption = figure.caption.replace("\\", "\\\\").replace('"', '\\"').strip()
    return f'![{alt}](<{figure.src}> "{caption}")'


def insert_figures(body: str, figures: list[Figure]) -> str:
    """Insert each figure after its paragraph; figures for one paragraph keep input order."""
    by_paragraph: dict[int, list[Figure]] = {}
    for figure in figures:
        by_paragraph.setdefault(figure.after_paragraph, []).append(figure)
    output: list[str] = []
    paragraph_number = 0
    for block in _blocks(body):
        output.append(block)
        if not _is_paragraph(block):
            continue
        paragraph_number += 1
        output.extend(figure_markdown(f) for f in by_paragraph.get(paragraph_number, []))
    return "\n\n".join(output)


def target_figure_count(body: str) -> int:
    """2 figures for short articles, up to 5 for long ones."""
    length = len(body)
    if length < 3000:
        return 2
    if length < 6000:
        return 3
    if length < 12000:
        return 4
    return 5


def _numbered_listing(body: str) -> str:
    return "\n\n".join(f"[{index}] {text}" for index, text in enumerate(numbered_paragraphs(body), 1))


def extract_article_images(html: str) -> list[ArticleImage]:
    """Body images of a WordPress post (`wp-image-*` class), deduplicated, in page order.

    Each image carries the text that precedes it on the page as context,
    so a model can tell which translated paragraph it belongs next to.
    """
    root = lxml.html.fromstring(html)
    images: list[ArticleImage] = []
    seen: set[str] = set()
    recent_text = ""
    for element in root.iter():
        if not isinstance(element.tag, str):
            continue
        if element.tag in {"p", "h2", "h3", "h4", "li"}:
            text = " ".join(element.text_content().split())
            if text:
                recent_text = f"{recent_text} {text}"[-600:]
            continue
        if element.tag != "img" or "wp-image" not in (element.get("class") or ""):
            continue
        src = element.get("src") or ""
        if not src or src in seen:
            continue
        seen.add(src)
        images.append(ArticleImage(src=src, alt=(element.get("alt") or "").strip(), context=recent_text.strip()))
    return images


def plan_article_figures(
    body: str, images: list[ArticleImage], planner: FigurePlanner, *, credit: str
) -> list[Figure]:
    """Place every original image; ones the model skips are spread evenly as a fallback."""
    if not images:
        return []
    paragraph_count = len(numbered_paragraphs(body))
    listing = "\n".join(
        f"[{index}] 그림 설명: {image.alt or '없음'} / 앞 문맥: {image.context}"
        for index, image in enumerate(images)
    )
    response = planner.plan(f"한국어 문단:\n{_numbered_listing(body)}\n\n원문 그림:\n{listing}")
    chosen: dict[int, Figure] = {}
    for item in response.get("figures", []):
        index, paragraph = item.get("image"), item.get("paragraph")
        if not isinstance(index, int) or not 0 <= index < len(images) or index in chosen:
            continue
        if not isinstance(paragraph, int) or not 1 <= paragraph <= paragraph_count:
            continue
        chosen[index] = Figure(
            after_paragraph=paragraph,
            src=images[index].src,
            alt=item["alt"].strip() or images[index].alt,
            caption=f"{item['caption'].strip()} 출처: {credit}",
        )
    for index, image in enumerate(images):
        if index not in chosen:
            fallback = max(1, round((index + 1) * paragraph_count / (len(images) + 1)))
            chosen[index] = Figure(fallback, image.src, image.alt, f"원문 그림: {image.alt} 출처: {credit}")
    return [chosen[index] for index in range(len(images))]


def _clock(seconds: int) -> str:
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def plan_video_figures(
    body: str, transcript: Transcript, planner: FigurePlanner, *, count: int
) -> list[PlannedFrame]:
    """Pick paragraphs to illustrate with frames; timestamps come from verified quotes only."""
    paragraph_count = len(numbered_paragraphs(body))
    captions = "\n".join(f"[{_clock(int(s.start))}] {s.text}" for s in transcript.segments)
    response = planner.plan(
        f"문단을 {count + 2}개 고르세요(중요한 순서대로).\n\n"
        f"한국어 문단:\n{_numbered_listing(body)}\n\n영어 자막:\n{captions}"
    )
    planned: list[PlannedFrame] = []
    for item in response.get("figures", []):
        paragraph = item.get("paragraph")
        if not isinstance(paragraph, int) or not 1 <= paragraph <= paragraph_count:
            continue
        match = verify_quote_against_transcript(item.get("quote", ""), transcript)
        start = match.anchor.start
        if match.score < MIN_QUOTE_SCORE or start is None:
            continue
        if any(abs(start - p.start) < MIN_FRAME_GAP_SECONDS for p in planned):
            continue
        caption = f"{item['caption'].strip()} (영상 {_clock(start)})"
        planned.append(PlannedFrame(paragraph, start, item["alt"].strip(), caption))
        if len(planned) == count:
            break
    return sorted(planned, key=lambda p: (p.after_paragraph, p.start))


_VIDEO_FORMAT = "bv*[height<=720][vcodec^=avc1]/bv*[height<=720][ext=mp4]/bv*[height<=720]/b"
_FRAME_OFFSETS = (1, 3, 6)
_FRAME_FILE = re.compile(r"\(</figures/(?P<source>[^/>]+)/(?P<minute>\d{2})-(?P<second>\d{2})\.jpg>")

FRAME_PICK_PROMPT = """첨부한 영상 장면 후보 중 블로그 글에 넣기 가장 좋은 한 장을 고르세요.
화면 글자나 슬라이드가 끝까지 온전히 보이고, 장면 전환·흔들림·눈 감은 순간이 없는 장면을 우선하세요.
첫 번째 이미지가 0번입니다."""
FRAME_PICK_SCHEMA = {
    "type": "object",
    "properties": {"best": {"type": "integer"}},
    "required": ["best"],
    "additionalProperties": False,
}


class FramePicker(Protocol):
    def pick(self, frames: list[Path]) -> int: ...


class CLIFramePicker:
    """Chooses the clearest of several candidate frames with a local model CLI."""

    def __init__(self, provider: str) -> None:
        self.provider = provider

    def pick(self, frames: list[Path]) -> int:
        result = run_structured_cli(
            self.provider, system_prompt=FRAME_PICK_PROMPT, user_prompt=f"후보 {len(frames)}장",
            schema=FRAME_PICK_SCHEMA, images=frames,
        )
        return result["best"]


def frame_times(body: str, source_id: str) -> list[int]:
    """Start seconds of the captured frames an article already references."""
    return [
        int(match["minute"]) * 60 + int(match["second"])
        for match in _FRAME_FILE.finditer(body)
        if match["source"] == source_id
    ]


def choose_best_frame(candidates: list[Path], output: Path, picker: FramePicker) -> None:
    """Copy the picked candidate to `output`; an out-of-range pick falls back to the middle one."""
    index = picker.pick(candidates)
    if not 0 <= index < len(candidates):
        index = len(candidates) // 2
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(candidates[index], output)


@lru_cache(maxsize=8)
def _stream_url(video_id: str) -> str:
    result = subprocess.run(
        ["yt-dlp", "-g", "-f", _VIDEO_FORMAT, f"https://www.youtube.com/watch?v={video_id}"],
        capture_output=True, text=True, timeout=120, check=True,
    )
    return result.stdout.strip().splitlines()[0]


def _grab_frames(source: str, base: float, directory: Path) -> list[Path]:
    """One JPEG per offset in `_FRAME_OFFSETS` after `base` seconds of `source`."""
    frames: list[Path] = []
    for offset in _FRAME_OFFSETS:
        frame = directory / f"candidate-{offset}.jpg"
        result = subprocess.run(
            ["ffmpeg", "-loglevel", "error", "-y", "-ss", str(base + offset), "-i", source,
             "-frames:v", "1", "-vf", "scale=1280:-2", "-q:v", "4", str(frame)],
            capture_output=True, timeout=180,
        )
        if result.returncode == 0 and frame.is_file() and frame.stat().st_size > 0:
            frames.append(frame)
    return frames


def capture_youtube_frame(video_id: str, start: int, output: Path, picker: FramePicker) -> None:
    """Save the clearest of three frames from just after `start` as a JPEG.

    Reading the stream URL directly is fast but YouTube rejects some of those
    URLs (403), so on failure yt-dlp downloads just that section instead.
    """
    with tempfile.TemporaryDirectory(prefix="atlas-frame-") as temp:
        directory = Path(temp)
        frames = _grab_frames(_stream_url(video_id), start, directory)
        if len(frames) < len(_FRAME_OFFSETS):
            clip = directory / "clip.mp4"
            subprocess.run(
                ["yt-dlp", "-q", "-f", _VIDEO_FORMAT, "--download-sections",
                 f"*{start}-{start + max(_FRAME_OFFSETS) + 2}", "-o", str(clip),
                 f"https://www.youtube.com/watch?v={video_id}"],
                capture_output=True, timeout=300,
            )
            frames = _grab_frames(str(clip), 0, directory) if clip.is_file() else []
        if not frames:
            raise RuntimeError(f"could not capture a frame of {video_id} at {start}s")
        choose_best_frame(frames, output, picker)


def recapture_frames(
    content_root: Path, public_dir: Path, source_id: str, capture_frame: Callable[[str, int, Path], None]
) -> int:
    """Re-capture every frame an article references, keeping its timestamps and text."""
    source = read_source(content_root, source_id)
    body = parse(article_path(content_root, source_id).read_text(encoding="utf-8")).body
    times = frame_times(body, source_id)
    for start in times:
        name = _clock(start).replace(":", "-") + ".jpg"
        capture_frame(source.youtube_id or "", start, public_dir / "figures" / source_id / name)
    return len(times)


def fetch_page_html(url: str) -> str:
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0 founder-atlas"}, timeout=30)
    response.raise_for_status()
    return response.text


def add_figures_to_source(
    content_root: Path,
    public_dir: Path,
    source_id: str,
    planner: FigurePlanner,
    *,
    capture_frame: Callable[[str, int, Path], None],
    fetch_html: Callable[[str], str] | None,
    search_figures: Callable[[str, int], list[Figure]] | None = None,
    force: bool = False,
) -> FigureResult:
    """Add figures to one source article, rewriting any figures it already has only with `force`.

    Blog posts and essays with fewer than `MIN_FIGURES` original images are
    topped up by `search_figures`; with none at all it fills the full target.
    """
    path = article_path(content_root, source_id)
    article = parse(path.read_text(encoding="utf-8"))
    if has_figures(article.body) and not force:
        return FigureResult(source_id, "skipped", 0)
    body = strip_figures(article.body)
    source = read_source(content_root, source_id)

    figures: list[Figure] = []
    if source.format == "video" and source.youtube_id:
        transcript = read_transcript(content_root, source_id)
        frames = (
            plan_video_figures(body, transcript, planner, count=target_figure_count(body))
            if transcript.kind == "segments"
            else []
        )
        for frame in frames:
            name = _clock(frame.start).replace(":", "-") + ".jpg"
            capture_frame(source.youtube_id, frame.start, public_dir / "figures" / source_id / name)
            figures.append(Figure(frame.after_paragraph, f"/figures/{source_id}/{name}", frame.alt, frame.caption))
        # Videos without captions (or unmatched quotes) are topped up with search images.
        if search_figures is not None and len(figures) < MIN_FIGURES:
            figures = [*figures, *search_figures(body, MIN_FIGURES - len(figures))]
    elif fetch_html is not None:
        try:
            images = extract_article_images(fetch_html(source.url))
        except requests.RequestException as exc:
            # Essays rarely have images; a flaky original page should not block search.
            print(f"[warn] {source_id}: original page unavailable, using search only ({exc})", file=sys.stderr)
            images = []
        credit = _ORIGIN_CREDITS.get(source.origin, source.origin)
        figures = plan_article_figures(body, images, planner, credit=credit)
        missing = target_figure_count(body) if not figures else MIN_FIGURES - len(figures)
        if search_figures is not None and missing > 0:
            figures = [*figures, *search_figures(body, missing)]

    if not figures:
        return FigureResult(source_id, "no-figures", 0)
    path.write_text(dump(article.frontmatter, insert_figures(body, figures)), encoding="utf-8")
    return FigureResult(source_id, "written" if len(figures) >= MIN_FIGURES else "partial", len(figures))
