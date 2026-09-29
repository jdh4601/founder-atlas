import { browseCategories, sortByPublished, toBrowseSources } from "./sourceBrowse";
import type { Source, Taxonomy } from "./types";

const taxonomy: Taxonomy = {
  categories: [
    {
      slug: "sales",
      title: "고객·세일즈",
      color: "#81B29A",
      keywords: [
        { slug: "first-customers", title: "첫 고객 확보" },
        { slug: "enterprise-sales", title: "엔터프라이즈 영업" },
      ],
    },
    {
      slug: "pricing",
      title: "가격·수익 모델",
      color: "#9B5DE5",
      keywords: [{ slug: "pricing-strategy", title: "가격 책정" }],
    },
  ],
};

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

it("turns article keyword slugs into titled tags and drops unknown ones", () => {
  const [result] = toBrowseSources(
    [source({ titleKo: "첫 고객 찾기", tags: ["first-customers", "고객", "pricing-strategy"] })],
    taxonomy,
  );

  expect(result.tags).toEqual([
    { slug: "first-customers", title: "첫 고객 확보" },
    { slug: "pricing-strategy", title: "가격 책정" },
  ]);
  expect(result.title).toBe("첫 고객 찾기");
});

it("does not guess tags for an article without keyword tags", () => {
  const [result] = toBrowseSources([source({ title: "Pricing and Sales" })], taxonomy);
  expect(result.tags).toEqual([]);
});

it("labels insight notes", () => {
  const [result] = toBrowseSources([source({ origin: "insights", format: "blog" })], taxonomy);
  expect(result.origin).toBe("인사이트");
});

it("sorts by publish date either way and keeps undated sources last", () => {
  const sources = toBrowseSources(
    [
      source({ id: "undated", published: null }),
      source({ id: "older", published: "2021-01-01" }),
      source({ id: "newer", published: "2024-01-01" }),
    ],
    taxonomy,
  );

  expect(sortByPublished(sources, "newest").map(({ id }) => id)).toEqual(["newer", "older", "undated"]);
  expect(sortByPublished(sources, "oldest").map(({ id }) => id)).toEqual(["older", "newer", "undated"]);
});

it("counts contents per keyword and hides keywords and categories with none", () => {
  const sources = toBrowseSources(
    [
      source({ id: "a", tags: ["first-customers"] }),
      source({ id: "b", tags: ["first-customers", "enterprise-sales"] }),
    ],
    taxonomy,
  );

  expect(browseCategories(taxonomy, sources, new Set(["enterprise-sales"]))).toEqual([
    {
      slug: "sales",
      title: "고객·세일즈",
      color: "#81B29A",
      count: 2,
      keywords: [
        { slug: "first-customers", title: "첫 고객 확보", count: 2, hasPage: false },
        { slug: "enterprise-sales", title: "엔터프라이즈 영업", count: 1, hasPage: true },
      ],
    },
  ]);
});
