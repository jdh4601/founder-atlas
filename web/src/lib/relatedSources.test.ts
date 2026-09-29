import { relatedSources } from "./relatedSources";
import type { Advice, Source, Taxonomy } from "./types";

const taxonomy: Taxonomy = {
  categories: [{ slug: "pricing", title: "가격", color: "#9B5DE5", keywords: [{ slug: "pricing-strategy", title: "가격 책정" }] }],
};

function source(id: string, title: string, origin: Source["origin"] = "a16z", tags: string[] = []): Source {
  return {
    id, title, titleKo: title, url: `https://example.com/${id}`,
    origin, format: "blog", youtubeId: null, published: "2026-01-01",
    speakers: [], thumbnail: null, images: [], ingestedAt: "2026-01-01", summary: "", tags,
  };
}

function advice(sourceId: string, keyword: string): Advice {
  return {
    id: `${sourceId}--01`, source: sourceId, category: "pricing", keywords: [keyword],
    context: { stage: [], domain: [] }, speaker: null, claim: "", body: "",
    anchor: { kind: "paragraph", paragraph: 0 }, matchScore: 100,
  };
}

it("prioritizes shared advice keywords and tags, excludes the current page, and returns two links", () => {
  const current = source("current", "AI Pricing Strategy", "a16z", ["pricing-strategy"]);
  const keywordMatch = source("keyword-match", "Fundraising Basics", "paul-graham");
  const tagMatch = source("tag-match", "AI Product Pricing", "a16z", ["pricing-strategy"]);
  const fallback = source("fallback", "Building a Startup");
  const results = relatedSources(
    current,
    [current, fallback, tagMatch, keywordMatch],
    [advice("current", "pricing-strategy"), advice("keyword-match", "pricing-strategy")],
    taxonomy,
  );

  expect(results.map((item) => item.id)).toEqual(["keyword-match", "tag-match"]);
});

it("still returns two distinct related pages when there are no shared tags", () => {
  const current = source("current", "Alpha");
  const results = relatedSources(current, [current, source("one", "Beta"), source("two", "Gamma")], [], taxonomy);
  expect(results.map((item) => item.id).sort()).toEqual(["one", "two"]);
});
