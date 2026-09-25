import path from "node:path";
import { getBacklinksFor } from "./backlinks";
import { loadKeywordPages } from "./keywords";

const FIXTURES_DIR = path.join(__dirname, "../../__fixtures__/content");

describe("getBacklinksFor", () => {
  const pages = loadKeywordPages(FIXTURES_DIR);

  it("finds pages whose body links [[slug]] to the target", () => {
    const backlinks = getBacklinksFor(pages, "pricing-strategy");
    expect(backlinks.map((p) => p.slug).sort()).toEqual(
      ["first-customers", "unit-economics"].sort(),
    );
  });

  it("returns an empty array when nothing links to the slug", () => {
    const backlinks = getBacklinksFor(pages, "not-a-real-slug");
    expect(backlinks).toEqual([]);
  });

  it("does not include the page itself even if it self-links", () => {
    const backlinks = getBacklinksFor(pages, "unit-economics");
    expect(backlinks.some((p) => p.slug === "unit-economics")).toBe(false);
  });
});
