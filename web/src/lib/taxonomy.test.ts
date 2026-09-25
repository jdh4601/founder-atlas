import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import {
  findCategory,
  findCategoryForKeyword,
  findKeywordTitle,
  loadTaxonomy,
} from "./taxonomy";

const FIXTURES_DIR = path.join(__dirname, "../../__fixtures__/content");

describe("loadTaxonomy", () => {
  it("parses the fixture taxonomy into exactly 8 categories", () => {
    const taxonomy = loadTaxonomy(FIXTURES_DIR);
    expect(taxonomy.categories).toHaveLength(8);
  });

  it("keeps category color and keyword titles intact", () => {
    const taxonomy = loadTaxonomy(FIXTURES_DIR);
    const pricing = taxonomy.categories.find((c) => c.slug === "pricing");
    expect(pricing?.title).toBe("가격·수익 모델");
    expect(pricing?.color).toBe("#9B5DE5");
    expect(pricing?.keywords).toContainEqual({
      slug: "pricing-strategy",
      title: "가격 책정",
    });
  });

  it("throws a clear error when a taxonomy file does not have 8 categories", () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "taxonomy-test-"));
    fs.writeFileSync(
      path.join(dir, "taxonomy.yaml"),
      "categories:\n  - slug: idea\n    title: 아이디어\n    color: '#111111'\n    keywords: []\n",
    );
    expect(() => loadTaxonomy(dir)).toThrow(/Invalid taxonomy/);
  });
});

describe("findCategory / findKeywordTitle", () => {
  const taxonomy = loadTaxonomy(FIXTURES_DIR);

  it("finds a category by slug", () => {
    expect(findCategory(taxonomy, "pricing")?.title).toBe("가격·수익 모델");
  });

  it("returns undefined for an unknown category slug", () => {
    expect(findCategory(taxonomy, "not-a-category")).toBeUndefined();
  });

  it("finds a keyword title by slug across all categories", () => {
    expect(findKeywordTitle(taxonomy, "first-customers")).toBe("첫 고객 확보");
  });

  it("returns undefined for an unknown keyword slug", () => {
    expect(findKeywordTitle(taxonomy, "not-a-keyword")).toBeUndefined();
  });

  it("finds the category that owns a keyword slug", () => {
    expect(findCategoryForKeyword(taxonomy, "pricing-strategy")?.slug).toBe(
      "pricing",
    );
  });

  it("returns undefined when no category owns the keyword slug", () => {
    expect(
      findCategoryForKeyword(taxonomy, "not-a-keyword"),
    ).toBeUndefined();
  });
});
