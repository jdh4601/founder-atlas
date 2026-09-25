import path from "node:path";
import { getSourceById, loadSources } from "./sources";

const FIXTURES_DIR = path.join(__dirname, "../../__fixtures__/content");

describe("loadSources", () => {
  it("loads all 3 fixture sources", () => {
    const sources = loadSources(FIXTURES_DIR);
    expect(sources).toHaveLength(3);
  });

  it("maps frontmatter snake_case fields to camelCase", () => {
    const sources = loadSources(FIXTURES_DIR);
    const video = sources.find(
      (s) => s.id === "yc-youtube-sample-pricing-lesson",
    );
    expect(video).toBeDefined();
    expect(video?.titleKo).toBe("제품 가격을 정하는 법 (샘플)");
    expect(video?.youtubeId).toBe("SAMPLE0001A");
    expect(video?.format).toBe("video");
    expect(video?.origin).toBe("yc-youtube");
    expect(video?.ingestedAt).toBe("2026-09-25");
    expect(video?.summary).toContain("샘플 데이터");
  });

  it("keeps youtubeId and thumbnail null for the essay source", () => {
    const sources = loadSources(FIXTURES_DIR);
    const essay = sources.find(
      (s) => s.id === "paul-graham-sample-do-things-that-dont-scale",
    );
    expect(essay?.youtubeId).toBeNull();
    expect(essay?.thumbnail).toBeNull();
    expect(essay?.format).toBe("essay");
  });
});

describe("getSourceById", () => {
  it("finds a source by id", () => {
    const sources = loadSources(FIXTURES_DIR);
    const found = getSourceById(
      sources,
      "lightcone-sample-enterprise-first-customers",
    );
    expect(found?.origin).toBe("lightcone");
  });

  it("returns undefined for an unknown id", () => {
    const sources = loadSources(FIXTURES_DIR);
    expect(getSourceById(sources, "does-not-exist")).toBeUndefined();
  });
});
