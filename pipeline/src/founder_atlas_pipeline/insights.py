"""Import Obsidian insight notes (`07_Insights/`) as sources with Korean articles.

Each note already is a Korean summary, so its numbered insight sections become
the article body as-is. Personal sections (why it matters to me, linked notes,
to-dos, the original backlink) are dropped, and `[[wikilinks]]` become plain
text. A model writes only the founder-facing title, one-line summary, lead,
and topic tags, from the cleaned body alone.
"""

from __future__ import annotations

import hashlib
import re
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Protocol
from urllib.parse import parse_qs, urlparse

import requests

from founder_atlas_pipeline.cli_providers import run_structured_cli
from founder_atlas_pipeline.figures import numbered_paragraphs
from founder_atlas_pipeline.frontmatter import ParsedMarkdown, dump, parse
from founder_atlas_pipeline.ingest.fetchers import FetchError
from founder_atlas_pipeline.models import SourceMeta, Transcript, TranscriptSegment
from founder_atlas_pipeline.source_articles import article_path
from founder_atlas_pipeline.sources import write_source

ORIGIN = "insights"
TOPIC_TAGS = ("고객", "투자", "AI", "성장", "제품", "영업", "가격", "아이디어", "채용")
_PERSONAL_HEADING = re.compile(
    r"유효한가|왜 유용한가|연결되는 인사이트|관련 노트|원문|원본|적용할|할 것|바꿀 것|실행 메모|자기평가|더 공부"
)
_WIKILINK = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
_URL = re.compile(r"https?://[^\s\"')\]>]+")
_YOUTUBE_URL = re.compile(r"https?://(?:www\.)?(?:youtube\.com/watch\?[^\s\"')\]>]+|youtu\.be/[^\s\"')\]>]+)")

SYSTEM_PROMPT = """당신은 창업가를 위한 아카이브의 편집자입니다.
아래 한국어 인사이트 노트만 근거로, 창업가가 목록에서 보고 바로 도움을 얻을 제목을 쓰세요.
"누구누구 인터뷰", "OO 강연"처럼 사람이나 형식을 내세우지 말고, 노트의 가장 중요한 교훈을
실행 가능한 주장으로 40자 이내에 쓰세요(예: "매출보다 IP가 쌓이는 사업을 남겨라").
tldr은 핵심을 압축한 한 문장, lead는 글을 여는 1~2문장 도입입니다.
tags는 다음 목록에서 노트 주제와 직접 관련된 것만 0~3개 고르세요: 고객, 투자, AI, 성장, 제품, 영업, 가격, 아이디어, 채용.
노트에 없는 사실이나 수치를 지어내지 마세요."""

SCHEMA = {
    "type": "object",
    "properties": {
        "title_ko": {"type": "string"},
        "tldr": {"type": "string"},
        "lead": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["title_ko", "tldr", "lead", "tags"],
    "additionalProperties": False,
}


class InsightWriter(Protocol):
    def write(self, prompt: str) -> dict: ...


class TranscriptSource(Protocol):
    def fetch_segments(self, video_id: str) -> list[TranscriptSegment]: ...


class CLIInsightWriter:
    def __init__(self, provider: str) -> None:
        self.provider = provider

    def write(self, prompt: str) -> dict:
        return run_structured_cli(self.provider, system_prompt=SYSTEM_PROMPT, user_prompt=prompt, schema=SCHEMA)


class AnyLanguageTranscripts:
    """YouTube captions in Korean or English, whichever the video has."""

    def fetch_segments(self, video_id: str) -> list[TranscriptSegment]:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api._errors import CouldNotRetrieveTranscript, RequestBlocked

        try:
            fetched = YouTubeTranscriptApi().fetch(video_id, languages=["ko", "en", "en-US"])
        except (CouldNotRetrieveTranscript, RequestBlocked) as error:
            raise FetchError(f"no Korean or English captions for {video_id}") from error
        return [TranscriptSegment(float(s.start), float(s.duration), s.text) for s in fetched]


@dataclass(frozen=True)
class InsightResult:
    source_id: str
    status: str  # written | skipped
    note: str


def _plain_links(text: str) -> str:
    return _WIKILINK.sub(lambda m: m[2] or Path(m[1]).name.removesuffix(".md"), text)


def clean_note_body(body: str) -> str:
    """Keep the insight sections; drop personal sections, horizontal rules, and wikilinks."""
    kept: list[str] = []
    skipping = False
    for line in body.splitlines():
        if line.startswith("## "):
            is_numbered = bool(re.match(r"## \d", line))
            skipping = not is_numbered and bool(_PERSONAL_HEADING.search(line))
        if skipping or line.strip() == "---":
            continue
        kept.append(_plain_links(line))
    text = "\n".join(kept)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def youtube_id_from_url(url: str) -> str | None:
    parsed = urlparse(url)
    host = parsed.netloc.lower().removeprefix("www.")
    if host == "youtu.be":
        return parsed.path.strip("/")[:11] or None
    if host.endswith("youtube.com"):
        return (parse_qs(parsed.query).get("v") or [None])[0]
    return None


def _first_url(text: str) -> str | None:
    youtube = _YOUTUBE_URL.search(text)
    if youtube:
        return youtube[0]
    match = _URL.search(text)
    return match[0] if match else None


def find_source_url(frontmatter: dict, body: str, vault: Path) -> str | None:
    """The note's original: `original`, a URL in `source`, the linked clipping's URL, or the body."""
    original = str(frontmatter.get("original") or "")
    if _URL.search(original):
        return _first_url(original)
    source = str(frontmatter.get("source") or "")
    if _URL.search(source):
        return _first_url(source)
    link = _WIKILINK.search(source)
    if link:
        clipping = vault / link[1]
        clipping = clipping if clipping.suffix == ".md" else clipping.with_name(clipping.name + ".md")
        if clipping.is_file():
            meta = parse(clipping.read_text(encoding="utf-8")).frontmatter
            for key in ("source", "url", "original"):
                if _URL.search(str(meta.get(key) or "")):
                    return _first_url(str(meta[key]))
    return _first_url(body)


def insight_source_id(filename: str, taken: set[str]) -> str:
    """`insights-{NNN}` from the note's number prefix; later duplicates get `-2`, `-3`."""
    number = re.match(r"(\d+)", filename)
    base = f"{ORIGIN}-{number[1] if number else hashlib.sha1(filename.encode()).hexdigest()[:8]}"
    candidate, suffix = base, 2
    while candidate in taken:
        candidate, suffix = f"{base}-{suffix}", suffix + 1
    return candidate


def youtube_thumbnail(video_id: str) -> str:
    """The 16:9 `maxresdefault` thumbnail when YouTube has one, else `hqdefault`."""
    maxres = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
    try:
        if requests.head(maxres, timeout=15).status_code == 200:
            return maxres
    except requests.RequestException:
        pass
    return f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"


def _speakers(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return [str(value).strip()] if value else []


def _parse_note(text: str) -> ParsedMarkdown:
    """Notes may be plain Markdown with no frontmatter at all."""
    if text.startswith("---"):
        return parse(text)
    return ParsedMarkdown(frontmatter={}, body=text)


def import_insight_note(
    content_root: Path,
    vault: Path,
    note: Path,
    writer: InsightWriter,
    *,
    youtube: TranscriptSource,
    thumbnail_for: Callable[[str], str | None],
    source_id: str | None = None,
    force: bool = False,
) -> InsightResult:
    """Write `sources/{id}.md`, its transcript, and `source_articles/{id}.md` for one note."""
    source_id = source_id or insight_source_id(note.name, set())
    # The article is written last, so its presence marks a finished import.
    if article_path(content_root, source_id).is_file() and not force:
        return InsightResult(source_id, "skipped", note.name)
    parsed = _parse_note(note.read_text(encoding="utf-8"))
    body = clean_note_body(parsed.body)
    url = find_source_url(parsed.frontmatter, parsed.body, vault) or ""
    video_id = youtube_id_from_url(url) if url else None

    transcript = Transcript(kind="paragraphs", paragraphs=numbered_paragraphs(body))
    if video_id:
        try:
            transcript = Transcript(kind="segments", segments=youtube.fetch_segments(video_id))
        except FetchError as exc:
            # Captions are optional: the note text stands in, and figures fall back to search.
            print(f"[warn] {note.name}: {exc}", file=sys.stderr)

    meta = SourceMeta(
        id=source_id,
        title=str(parsed.frontmatter.get("title") or re.sub(r"^\d+_", "", note.stem)),
        title_ko="",
        url=url,
        origin=ORIGIN,
        format="video" if video_id else "blog",
        published=str(parsed.frontmatter["created"]) if parsed.frontmatter.get("created") else None,
        speakers=_speakers(parsed.frontmatter.get("speaker")),
        thumbnail=thumbnail_for(video_id) if video_id else None,
        images=[],
        ingested_at=date.today().isoformat(),
        summary_ko="",
        youtube_id=video_id,
    )
    write_source(content_root, meta, transcript)

    written = writer.write(f"노트 제목: {meta.title}\n\n노트 본문:\n{body}")
    tags = [tag for tag in written.get("tags", []) if tag in TOPIC_TAGS][:3]
    frontmatter = {
        "source": source_id,
        "title_ko": written["title_ko"].strip(),
        "tldr": written["tldr"].strip(),
        "lead": written["lead"].strip(),
        "tags": tags,
        "source_sha256": hashlib.sha256(note.read_bytes()).hexdigest(),
        "generated_at": date.today().isoformat(),
    }
    output = article_path(content_root, source_id)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(dump(frontmatter, body), encoding="utf-8")
    return InsightResult(source_id, "written", note.name)


EXCLUDE_FILE = "insights-exclude.txt"


def load_excluded_ids(content_root: Path) -> set[str]:
    """Source ids listed in `content/insights-exclude.txt`, one per line; `#` starts a comment."""
    path = content_root / EXCLUDE_FILE
    if not path.is_file():
        return set()
    lines = (line.split("#", 1)[0].strip() for line in path.read_text(encoding="utf-8").splitlines())
    return {line for line in lines if line}


def note_ids(notes: Iterable[Path], excluded: set[str] | frozenset[str] = frozenset()) -> list[tuple[Path, str]]:
    """Stable ids for notes in filename order, so duplicates keep the same suffix.

    Excluded ids are dropped after numbering, so excluding one note never
    shifts the id of another.
    """
    taken: set[str] = set()
    pairs = []
    for note in sorted(notes, key=lambda p: p.name):
        source_id = insight_source_id(note.name, taken)
        taken.add(source_id)
        if source_id not in excluded:
            pairs.append((note, source_id))
    return pairs
