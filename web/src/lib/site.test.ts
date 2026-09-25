import path from "node:path";
import { getSiteData } from "./site";

const FIXTURES_DIR = path.join(__dirname, "../../__fixtures__/content");

describe("getSiteData", () => {
  it("loads every content collection from the given content directory", () => {
    const site = getSiteData(FIXTURES_DIR);
    expect(site.taxonomy.categories).toHaveLength(8);
    expect(site.profile.stage).toBe("pre-seed");
    expect(site.keywordPages).toHaveLength(3);
    expect(site.advice).toHaveLength(8);
    expect(site.sources).toHaveLength(3);
  });
});
