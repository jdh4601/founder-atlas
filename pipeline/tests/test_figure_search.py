"""Search-based figures: model picks paragraphs and candidates, code fetches and credits."""

from __future__ import annotations

import html
import json
from pathlib import Path

from founder_atlas_pipeline.figures import Figure
from founder_atlas_pipeline.figure_search import (
    ImageCandidate,
    parse_bing_results,
    plan_search_figures,
)

BODY = """## 소제목

라멘 수익성이란 생활비만 버는 상태를 말한다.

성장은 스타트업의 본질이다.

마지막 문단이다."""


class QueuePlanner:
    def __init__(self, *responses: dict) -> None:
        self.responses = list(responses)
        self.prompts: list[str] = []

    def plan(self, prompt: str) -> dict:
        self.prompts.append(prompt)
        return self.responses.pop(0)


def _bing_item(murl: str, purl: str, title: str) -> str:
    payload = html.escape(json.dumps({"murl": murl, "purl": purl, "t": title}))
    return f'<a class="iusc" style="" m="{payload}" href="#">'


def test_parse_bing_results_drops_social_and_non_http_images() -> None:
    page = "".join(
        [
            _bing_item("https://blog.example.com/ramen.png", "https://blog.example.com/post", "Ramen profitable"),
            _bing_item("https://media.licdn.com/x.jpg", "https://www.linkedin.com/posts/1", "LinkedIn"),
            _bing_item("data:image/png;base64,AAA", "https://x.com", "inline"),
            _bing_item("https://blog.example.com/ramen.png", "https://blog.example.com/other", "dup"),
        ]
    )

    assert parse_bing_results(page) == [
        ImageCandidate("https://blog.example.com/ramen.png", "https://blog.example.com/post", "Ramen profitable")
    ]


class FakeReviewer:
    def __init__(self, verdicts: dict[str, bool]) -> None:
        self.verdicts = verdicts
        self.reviewed: list[str] = []

    def review(self, paragraph: str, image: Path) -> dict:
        self.reviewed.append(image.read_text())
        relevant = self.verdicts[image.read_text()]
        return {"relevant": relevant, "alt": "본 그림", "caption": f"실제 그림 설명 {image.read_text()}"}


def _search(query: str) -> list[ImageCandidate]:
    return [
        ImageCandidate(f"https://a.com/{query}-0.jpg", "https://a.com/p", "first"),
        ImageCandidate(f"https://www.b.org/{query}-1.jpg", "https://www.b.org/post", "second"),
        ImageCandidate(f"https://c.net/{query}-2.jpg", "https://c.net/post", "third"),
    ]


def _download(url: str, output: Path) -> bool:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(url.rsplit("/", 1)[1])
    return True


def test_plan_search_figures_tries_ranked_candidates_until_one_is_relevant(tmp_path: Path) -> None:
    planner = QueuePlanner(
        {
            "figures": [
                {"paragraph": 1, "query": "ramen", "alt": "라멘", "caption": "문단 기반 캡션"},
                {"paragraph": 2, "query": "growth", "alt": "성장", "caption": "성장"},
                {"paragraph": 7, "query": "out of range", "alt": "x", "caption": "x"},
            ]
        },
        {"choices": [{"figure": 0, "candidates": [1, 2]}, {"figure": 1, "candidates": []}]},
    )
    reviewer = FakeReviewer({"ramen-1.jpg": False, "ramen-2.jpg": True})

    figures = plan_search_figures(
        BODY, "pg-ramen", planner, reviewer, search=_search, download=_download, public_dir=tmp_path, count=2
    )

    assert reviewer.reviewed == ["ramen-1.jpg", "ramen-2.jpg"]
    assert figures == [
        Figure(1, "/figures/pg-ramen/web-1.jpg", "본 그림", "실제 그림 설명 ramen-2.jpg 출처: c.net")
    ]
    assert (tmp_path / "figures" / "pg-ramen" / "web-1.jpg").read_text() == "ramen-2.jpg"
    assert "second" in planner.prompts[1]


def test_plan_search_figures_skips_candidates_that_fail_to_download(tmp_path: Path) -> None:
    planner = QueuePlanner(
        {"figures": [{"paragraph": 2, "query": "growth", "alt": "a", "caption": "c"}]},
        {"choices": [{"figure": 0, "candidates": [0]}]},
    )

    figures = plan_search_figures(
        BODY,
        "s",
        planner,
        FakeReviewer({}),
        search=_search,
        download=lambda url, output: False,
        public_dir=tmp_path,
        count=2,
    )

    assert figures == []
