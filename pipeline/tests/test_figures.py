"""Figures are placed after Korean paragraphs; video timestamps come from code."""

from __future__ import annotations

from pathlib import Path

import pytest

from founder_atlas_pipeline.figures import (
    Figure,
    add_figures_to_source,
    choose_best_frame,
    frame_times,
    extract_article_images,
    insert_figures,
    numbered_paragraphs,
    plan_article_figures,
    plan_video_figures,
    strip_figures,
    target_figure_count,
)
from founder_atlas_pipeline.frontmatter import dump, parse
from founder_atlas_pipeline.models import SourceMeta, Transcript, TranscriptSegment
from founder_atlas_pipeline.sources import write_source

BODY = """## 첫 소제목

첫 문단입니다.

둘째 문단입니다.

## 둘째 소제목

셋째 문단입니다."""


class FakePlanner:
    def __init__(self, response: dict) -> None:
        self.response = response
        self.prompts: list[str] = []

    def plan(self, prompt: str) -> dict:
        self.prompts.append(prompt)
        return self.response


def test_numbered_paragraphs_skip_headings_and_figures() -> None:
    body = BODY.replace("둘째 문단입니다.", '둘째 문단입니다.\n\n![a](https://x/a.jpg "c")')
    assert numbered_paragraphs(body) == ["첫 문단입니다.", "둘째 문단입니다.", "셋째 문단입니다."]


def test_insert_figures_places_markdown_after_the_numbered_paragraph() -> None:
    figures = [
        Figure(after_paragraph=3, src="https://x/b.jpg", alt="그림 B", caption="캡션 B"),
        Figure(after_paragraph=1, src="/figures/s/01-05.jpg", alt="그림 A", caption='따옴표 "A"'),
    ]

    result = insert_figures(BODY, figures)

    assert result == (
        "## 첫 소제목\n\n첫 문단입니다.\n\n"
        '![그림 A](</figures/s/01-05.jpg> "따옴표 \\"A\\"")\n\n'
        "둘째 문단입니다.\n\n## 둘째 소제목\n\n셋째 문단입니다.\n\n"
        '![그림 B](<https://x/b.jpg> "캡션 B")'
    )


def test_insert_figures_is_idempotent_after_strip() -> None:
    figures = [Figure(after_paragraph=2, src="https://x/a.jpg", alt="A", caption="C")]
    once = insert_figures(BODY, figures)
    assert insert_figures(strip_figures(once), figures) == once
    assert strip_figures(once) == BODY


@pytest.mark.parametrize(
    ("length", "expected"), [(1000, 2), (4000, 3), (8000, 4), (20000, 5)]
)
def test_target_figure_count_scales_with_length(length: int, expected: int) -> None:
    assert target_figure_count("가" * length) == expected


def test_extract_article_images_keeps_only_body_images_in_order() -> None:
    html = """
    <html><body>
    <img src="https://cdn/logo.png" alt="logo">
    <article>
      <h2>Breaking down curves</h2>
      <p>Cohorts break into three sections.</p>
      <p><a href="#"><img class="alignnone wp-image-1" src="https://cdn/uploads/curve.jpg" alt="Curve"></a></p>
      <p>ChatGPT shows a smile.</p>
      <figure><img class="size-full wp-image-2" src="https://cdn/uploads/smile.jpg" alt=""></figure>
      <img class="wp-image-3" src="https://cdn/uploads/curve.jpg" alt="Curve again">
    </article>
    <img src="https://cdn/uploads/2023/04/author.png" alt="">
    </body></html>
    """

    images = extract_article_images(html)

    assert [image.src for image in images] == [
        "https://cdn/uploads/curve.jpg",
        "https://cdn/uploads/smile.jpg",
    ]
    assert images[0].alt == "Curve"
    assert "three sections" in images[0].context
    assert "smile" in images[1].context


def test_plan_article_figures_places_every_image_and_credits_source() -> None:
    images = extract_article_images(
        '<p>One</p><img class="wp-image-1" src="https://c/a.jpg" alt="A">'
        '<p>Two</p><img class="wp-image-2" src="https://c/b.jpg" alt="B">'
    )
    planner = FakePlanner(
        {"figures": [{"image": 1, "paragraph": 3, "alt": "B 설명", "caption": "B 캡션"}]}
    )

    figures = plan_article_figures(BODY, images, planner, credit="a16z")

    assert [(f.src, f.after_paragraph) for f in figures] == [
        ("https://c/a.jpg", 1),
        ("https://c/b.jpg", 3),
    ]
    assert figures[1].caption == "B 캡션 출처: a16z"
    assert figures[0].caption.endswith("출처: a16z")


def _transcript() -> Transcript:
    return Transcript(
        kind="segments",
        segments=[
            TranscriptSegment(start=0.0, duration=5.0, text="welcome to startup school"),
            TranscriptSegment(start=65.4, duration=5.0, text="you should talk to your users every week"),
            TranscriptSegment(start=190.2, duration=5.0, text="charge more than you think you should"),
        ],
    )


def test_plan_video_figures_computes_timestamps_from_verified_quotes_only() -> None:
    planner = FakePlanner(
        {
            "figures": [
                {"paragraph": 1, "quote": "talk to your users every week", "alt": "A", "caption": "사용자 대화"},
                {"paragraph": 3, "quote": "a sentence the speaker never said", "alt": "B", "caption": "지어낸 말"},
                {"paragraph": 2, "quote": "charge more than you think", "alt": "C", "caption": "가격"},
                {"paragraph": 9, "quote": "welcome to startup school", "alt": "D", "caption": "없는 문단"},
            ]
        }
    )

    planned = plan_video_figures(BODY, _transcript(), planner, count=3)

    assert [(p.start, p.after_paragraph) for p in planned] == [(65, 1), (190, 2)]
    assert planned[0].caption == "사용자 대화 (영상 01:05)"


def test_add_figures_to_video_source_captures_frames_and_writes_article(tmp_path: Path) -> None:
    content = tmp_path / "content"
    (content / "sources").mkdir(parents=True)
    source = SourceMeta(
        id="yc-youtube-users",
        title="Users",
        title_ko="",
        url="https://www.youtube.com/watch?v=abc",
        origin="yc-youtube",
        format="video",
        speakers=[],
        published=None,
        youtube_id="abc",
        thumbnail=None,
        images=[],
        ingested_at="2026-09-28",
        summary_ko="",
    )
    write_source(content, source, _transcript())
    article = content / "source_articles" / "yc-youtube-users.md"
    article.parent.mkdir()
    article.write_text(dump({"source": source.id, "title_ko": "사용자"}, BODY), encoding="utf-8")
    planner = FakePlanner(
        {
            "figures": [
                {"paragraph": 1, "quote": "talk to your users every week", "alt": "A", "caption": "대화"},
                {"paragraph": 3, "quote": "charge more than you think", "alt": "C", "caption": "가격"},
            ]
        }
    )
    captured: list[tuple[str, int, Path]] = []

    def capture(video_id: str, start: int, output: Path) -> None:
        captured.append((video_id, start, output))
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"jpg")

    result = add_figures_to_source(
        content, tmp_path / "public", source.id, planner, capture_frame=capture, fetch_html=None
    )

    assert result.status == "written"
    assert result.count == 2
    assert [(c[0], c[1]) for c in captured] == [("abc", 65), ("abc", 190)]
    assert captured[0][2] == tmp_path / "public" / "figures" / source.id / "01-05.jpg"
    body = parse(article.read_text(encoding="utf-8")).body
    assert '![A](</figures/yc-youtube-users/01-05.jpg> "대화 (영상 01:05)")' in body

    again = add_figures_to_source(
        content, tmp_path / "public", source.id, planner, capture_frame=capture, fetch_html=None
    )
    assert again.status == "skipped"


def _write_blog_source(tmp_path: Path, origin: str) -> Path:
    content = tmp_path / "content"
    (content / "sources").mkdir(parents=True)
    source = SourceMeta(
        id=f"{origin}-essay",
        title="Essay",
        title_ko="",
        url="https://example.com/essay",
        origin=origin,
        format="essay",
        speakers=[],
        published=None,
        thumbnail=None,
        images=[],
        ingested_at="2026-09-28",
        summary_ko="",
    )
    write_source(content, source, Transcript(kind="paragraphs", paragraphs=["text"]))
    article = content / "source_articles" / f"{origin}-essay.md"
    article.parent.mkdir()
    article.write_text(dump({"source": source.id, "title_ko": "글"}, BODY), encoding="utf-8")
    return content


@pytest.mark.parametrize(
    ("page", "expected_search_count"),
    [
        ("<p>No images here</p>", 2),
        ('<p>One</p><img class="wp-image-1" src="https://c/a.jpg" alt="A">', 1),
        (
            '<p>One</p><img class="wp-image-1" src="https://c/a.jpg" alt="A">'
            '<img class="wp-image-2" src="https://c/b.jpg" alt="B">',
            0,
        ),
    ],
)
def test_add_figures_searches_only_for_the_missing_minimum(
    tmp_path: Path, page: str, expected_search_count: int
) -> None:
    content = _write_blog_source(tmp_path, "paul-graham")
    requested: list[int] = []

    def search(body: str, count: int) -> list[Figure]:
        requested.append(count)
        return [Figure(2, f"/figures/s/web-{i}.jpg", "검색", "검색 캡션") for i in range(count)]

    result = add_figures_to_source(
        content,
        tmp_path / "public",
        "paul-graham-essay",
        FakePlanner({"figures": []}),
        capture_frame=lambda *args: None,
        fetch_html=lambda url: page,
        search_figures=search,
    )

    assert requested == ([expected_search_count] if expected_search_count else [])
    assert result.count == 2


def test_frame_times_in_markdown_are_read_back_from_local_frame_paths() -> None:
    body = (
        BODY
        + '\n\n![a](</figures/yc-x/01-05.jpg> "c")\n\n![b](<https://cdn/x.jpg> "d")'
        + '\n\n![c](</figures/yc-x/web-1.jpg> "e")\n\n![d](</figures/yc-x/12-00.jpg> "f")'
    )
    assert frame_times(body, "yc-x") == [65, 720]


def test_choose_best_frame_keeps_the_picked_candidate(tmp_path: Path) -> None:
    candidates = []
    for index in range(3):
        path = tmp_path / f"c{index}.jpg"
        path.write_text(f"frame {index}")
        candidates.append(path)
    output = tmp_path / "out.jpg"

    class Picker:
        def pick(self, frames: list[Path]) -> int:
            assert frames == candidates
            return 2

    choose_best_frame(candidates, output, Picker())

    assert output.read_text() == "frame 2"


def test_choose_best_frame_falls_back_to_the_middle_frame_on_a_bad_pick(tmp_path: Path) -> None:
    candidates = [tmp_path / f"c{i}.jpg" for i in range(3)]
    for index, path in enumerate(candidates):
        path.write_text(f"frame {index}")

    class Picker:
        def pick(self, frames: list[Path]) -> int:
            return 7

    choose_best_frame(candidates, tmp_path / "out.jpg", Picker())

    assert (tmp_path / "out.jpg").read_text() == "frame 1"
