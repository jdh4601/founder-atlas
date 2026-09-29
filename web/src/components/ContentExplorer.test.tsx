/** @jest-environment jsdom */

import { fireEvent, render, screen, within } from "@testing-library/react";
import { ContentExplorer } from "./ContentExplorer";
import type { BrowseCategory, BrowseSource } from "@/lib/sourceBrowse";

const categories: BrowseCategory[] = [
  {
    slug: "sales",
    title: "고객·세일즈",
    color: "#81B29A",
    count: 2,
    keywords: [
      { slug: "first-customers", title: "첫 고객 확보", count: 2, hasPage: true },
      { slug: "enterprise-sales", title: "엔터프라이즈 영업", count: 1, hasPage: false },
    ],
  },
  {
    slug: "pricing",
    title: "가격·수익 모델",
    color: "#9B5DE5",
    count: 1,
    keywords: [{ slug: "pricing-strategy", title: "가격 책정", count: 1, hasPage: false }],
  },
];

function browse(id: string, title: string, published: string | null, tags: BrowseSource["tags"]): BrowseSource {
  return { id, title, url: "", thumbnail: null, origin: "YC", format: "영상", published, speakers: [], tags };
}

const sources: BrowseSource[] = [
  browse("a", "첫 10명의 고객", "2024-01-01", [{ slug: "first-customers", title: "첫 고객 확보" }]),
  browse("b", "대기업에 파는 법", "2020-01-01", [
    { slug: "first-customers", title: "첫 고객 확보" },
    { slug: "enterprise-sales", title: "엔터프라이즈 영업" },
  ]),
  browse("c", "가격을 올려라", "2022-01-01", [{ slug: "pricing-strategy", title: "가격 책정" }]),
];

function cardTitles(): string[] {
  return within(screen.getByRole("list", { name: "콘텐츠 목록" }))
    .getAllByRole("heading")
    .map((heading) => heading.textContent ?? "");
}

it("filters contents by category tab and then by keyword chip", () => {
  render(<ContentExplorer categories={categories} sources={sources} />);
  expect(screen.getByText("3개 콘텐츠")).toBeInTheDocument();

  fireEvent.click(screen.getByRole("tab", { name: /고객·세일즈/ }));
  expect(screen.getByText("2개 콘텐츠")).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: /엔터프라이즈 영업/ }));
  expect(cardTitles()).toEqual(["대기업에 파는 법"]);

  fireEvent.click(screen.getByRole("button", { name: /엔터프라이즈 영업/ }));
  expect(screen.getByText("2개 콘텐츠")).toBeInTheDocument();

  fireEvent.click(screen.getByRole("tab", { name: "전체" }));
  expect(screen.getByText("3개 콘텐츠")).toBeInTheDocument();
});

it("links to the keyword page only when the selected keyword has one", () => {
  render(<ContentExplorer categories={categories} sources={sources} />);
  fireEvent.click(screen.getByRole("tab", { name: /고객·세일즈/ }));

  fireEvent.click(screen.getByRole("button", { name: /첫 고객 확보/ }));
  expect(screen.getByRole("link", { name: /키워드 페이지/ })).toHaveAttribute("href", "/k/first-customers");

  fireEvent.click(screen.getByRole("button", { name: /엔터프라이즈 영업/ }));
  expect(screen.queryByRole("link", { name: /키워드 페이지/ })).not.toBeInTheDocument();
});

it("sorts by date and searches titles", () => {
  render(<ContentExplorer categories={categories} sources={sources} />);
  expect(cardTitles()).toEqual(["첫 10명의 고객", "가격을 올려라", "대기업에 파는 법"]);

  fireEvent.change(screen.getByRole("combobox", { name: "정렬" }), { target: { value: "oldest" } });
  expect(cardTitles()).toEqual(["대기업에 파는 법", "가격을 올려라", "첫 10명의 고객"]);

  fireEvent.change(screen.getByRole("searchbox", { name: "콘텐츠 검색" }), { target: { value: "없는 제목" } });
  expect(screen.getByText(/일치하는 콘텐츠가 없습니다/)).toBeInTheDocument();
});

it("shows keyword titles as card hashtags", () => {
  render(<ContentExplorer categories={categories} sources={sources} />);
  expect(screen.getAllByText("#엔터프라이즈 영업")).toHaveLength(1);
});
