import path from "node:path";
import { getKeywordBySlug, loadKeywordPages } from "./keywords";

const FIXTURES_DIR = path.join(__dirname, "../../__fixtures__/content");

describe("loadKeywordPages", () => {
  it("loads all 3 fixture keyword pages", () => {
    const pages = loadKeywordPages(FIXTURES_DIR);
    expect(pages).toHaveLength(3);
  });

  it("parses frontmatter fields, including reviewed and advice ids", () => {
    const pages = loadKeywordPages(FIXTURES_DIR);
    const pricing = getKeywordBySlug(pages, "pricing-strategy");
    expect(pricing?.title).toBe("가격 책정");
    expect(pricing?.category).toBe("pricing");
    expect(pricing?.reviewed).toBe(true);
    expect(pricing?.advice).toContain(
      "yc-youtube-sample-pricing-lesson--01",
    );
    expect(pricing?.updatedAt).toBe("2026-09-25");
  });

  it("keeps reviewed: false pages as unreviewed", () => {
    const pages = loadKeywordPages(FIXTURES_DIR);
    const unitEconomics = getKeywordBySlug(pages, "unit-economics");
    expect(unitEconomics?.reviewed).toBe(false);
  });

  it("keeps raw markdown body with wikilinks/advice markers untransformed", () => {
    const pages = loadKeywordPages(FIXTURES_DIR);
    const pricing = getKeywordBySlug(pages, "pricing-strategy");
    expect(pricing?.body).toContain("[[unit-economics]]");
    expect(pricing?.body).toContain(
      "{{advice:yc-youtube-sample-pricing-lesson--01}}",
    );
    expect(pricing?.body).toContain("```mermaid");
  });

  it("parses image entries", () => {
    const pages = loadKeywordPages(FIXTURES_DIR);
    const pricing = getKeywordBySlug(pages, "pricing-strategy");
    expect(pricing?.images).toEqual([
      {
        src: "https://example.com/sample/thumbs/yc-pricing-lesson.jpg",
        alt: "[샘플] 가격 책정 강연 썸네일",
        source: "yc-youtube-sample-pricing-lesson",
      },
    ]);
  });
});

describe("getKeywordBySlug", () => {
  it("returns undefined for an unknown slug", () => {
    const pages = loadKeywordPages(FIXTURES_DIR);
    expect(getKeywordBySlug(pages, "does-not-exist")).toBeUndefined();
  });
});
