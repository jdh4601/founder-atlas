import { toBrowseSources } from "./sourceBrowse";
import type { Source } from "./types";

function source(overrides: Partial<Source>): Source {
  return {
    id: "one",
    title: "A Startup Essay",
    titleKo: "A Startup Essay",
    url: "https://example.com/one",
    origin: "paul-graham",
    format: "essay",
    youtubeId: null,
    published: null,
    speakers: [],
    thumbnail: null,
    images: [],
    ingestedAt: "2026-09-25",
    summary: "",
    ...overrides,
  };
}

it("uses source metadata and literal title terms for hashtags", () => {
  const [result] = toBrowseSources([
    source({ title: "Pricing and Sales", titleKo: "가격과 영업" }),
  ]);

  expect(result.tags).toEqual(["PaulGraham", "에세이", "가격", "영업"]);
  expect(result.title).toBe("가격과 영업");
});

it("does not infer topics from an unprocessed source's summary", () => {
  const [result] = toBrowseSources([
    source({ summary: "This article may mention pricing and fundraising." }),
  ]);
  expect(result.tags).toEqual(["PaulGraham", "에세이"]);
});

it("shows more recently published sources first", () => {
  const results = toBrowseSources([
    source({ id: "older", published: "2021-01-01" }),
    source({ id: "newer", published: "2024-01-01" }),
  ]);
  expect(results.map(({ id }) => id)).toEqual(["newer", "older"]);
});
