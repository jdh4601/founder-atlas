/** @jest-environment jsdom */

import { fireEvent, render, screen } from "@testing-library/react";
import { SourceBrowser } from "./SourceBrowser";
import type { BrowseSource } from "@/lib/sourceBrowse";

const sources: BrowseSource[] = [
  {
    id: "video",
    title: "고객 인터뷰",
    url: "https://example.com/video",
    thumbnail: null,
    origin: "YC",
    format: "영상",
    published: "2024-01-01",
    speakers: [],
    tags: ["YC", "영상", "고객"],
  },
  {
    id: "essay",
    title: "가격 책정",
    url: "https://example.com/essay",
    thumbnail: null,
    origin: "PaulGraham",
    format: "에세이",
    published: "2023-01-01",
    speakers: [],
    tags: ["PaulGraham", "에세이", "가격"],
  },
];

it("filters the content list by hashtag and title search", () => {
  render(<SourceBrowser sources={sources} />);
  expect(screen.getByText("2개 콘텐츠")).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: /#고객/ }));
  expect(screen.getByText("1개 콘텐츠")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /고객 인터뷰/ })).toBeInTheDocument();
  expect(screen.queryByRole("link", { name: /가격 책정/ })).not.toBeInTheDocument();

  fireEvent.change(screen.getByRole("searchbox", { name: "콘텐츠 검색" }), {
    target: { value: "없는 제목" },
  });
  expect(screen.getByText("0개 콘텐츠")).toBeInTheDocument();
  expect(screen.getByText(/일치하는 콘텐츠가 없습니다/)).toBeInTheDocument();
});
