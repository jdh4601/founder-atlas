import path from "node:path";
import {
  getAdviceById,
  getAdviceByIds,
  getAdviceForKeyword,
  loadAdvice,
  matchesProfile,
  sortAdviceByProfile,
} from "./advice";
import type { Profile } from "./types";

const FIXTURES_DIR = path.join(__dirname, "../../__fixtures__/content");

describe("loadAdvice", () => {
  it("loads all 8 fixture advice units", () => {
    const advice = loadAdvice(FIXTURES_DIR);
    expect(advice).toHaveLength(8);
  });

  it("never exposes the hidden `quote` field", () => {
    const advice = loadAdvice(FIXTURES_DIR);
    for (const unit of advice) {
      expect(unit).not.toHaveProperty("quote");
      expect(JSON.stringify(unit)).not.toMatch(/SAMPLE QUOTE/);
    }
  });

  it("maps a timestamp anchor correctly", () => {
    const advice = loadAdvice(FIXTURES_DIR);
    const unit = getAdviceById(
      advice,
      "yc-youtube-sample-pricing-lesson--01",
    );
    expect(unit?.anchor).toEqual({ kind: "timestamp", start: 120 });
  });

  it("maps a paragraph anchor correctly", () => {
    const advice = loadAdvice(FIXTURES_DIR);
    const unit = getAdviceById(
      advice,
      "paul-graham-sample-do-things-that-dont-scale--01",
    );
    expect(unit?.anchor).toEqual({ kind: "paragraph", paragraph: 2 });
  });

  it("keeps context stage/domain arrays, including empty = applies to all", () => {
    const advice = loadAdvice(FIXTURES_DIR);
    const wildcard = getAdviceById(
      advice,
      "yc-youtube-sample-pricing-lesson--02",
    );
    expect(wildcard?.context).toEqual({ stage: [], domain: [] });
  });

  it("keeps the Korean claim and body, and match score", () => {
    const advice = loadAdvice(FIXTURES_DIR);
    const unit = getAdviceById(
      advice,
      "yc-youtube-sample-pricing-lesson--01",
    );
    expect(unit?.claim).toBe("초기 B2B 제품은 가격을 낮추지 말고 높게 시작하라");
    expect(unit?.matchScore).toBe(96.5);
    expect(unit?.body).toContain("샘플 데이터");
  });
});

describe("getAdviceByIds", () => {
  it("returns advice in the same order as the given ids, skipping unknowns", () => {
    const advice = loadAdvice(FIXTURES_DIR);
    const result = getAdviceByIds(advice, [
      "yc-youtube-sample-pricing-lesson--02",
      "does-not-exist",
      "yc-youtube-sample-pricing-lesson--01",
    ]);
    expect(result.map((a) => a.id)).toEqual([
      "yc-youtube-sample-pricing-lesson--02",
      "yc-youtube-sample-pricing-lesson--01",
    ]);
  });
});

describe("getAdviceForKeyword", () => {
  it("returns every advice unit tagged with the given keyword", () => {
    const advice = loadAdvice(FIXTURES_DIR);
    const result = getAdviceForKeyword(advice, "first-customers");
    expect(result.map((a) => a.id).sort()).toEqual(
      [
        "lightcone-sample-enterprise-first-customers--01",
        "lightcone-sample-enterprise-first-customers--02",
        "paul-graham-sample-do-things-that-dont-scale--01",
      ].sort(),
    );
  });
});

describe("sortAdviceByProfile", () => {
  const profile: Profile = { stage: "pre-seed", domain: ["ai", "b2b"] };

  it("ranks advice matching stage/domain above advice that doesn't, treating empty context as applies-to-all", () => {
    const advice = loadAdvice(FIXTURES_DIR);
    const unitEconomicsAdvice = getAdviceForKeyword(advice, "unit-economics");
    const sorted = sortAdviceByProfile(unitEconomicsAdvice, profile);
    expect(sorted.map((a) => a.id)).toEqual([
      "yc-youtube-sample-pricing-lesson--02",
      "yc-youtube-sample-pricing-lesson--03",
      "lightcone-sample-enterprise-first-customers--03",
    ]);
  });

  it("keeps the original relative order for advice units that tie in score", () => {
    const advice = loadAdvice(FIXTURES_DIR);
    const firstCustomersAdvice = getAdviceForKeyword(advice, "first-customers");
    const sorted = sortAdviceByProfile(firstCustomersAdvice, profile);
    expect(sorted.map((a) => a.id)).toEqual(
      firstCustomersAdvice.map((a) => a.id),
    );
  });
});

describe("matchesProfile", () => {
  const profile: Profile = { stage: "pre-seed", domain: ["ai", "b2b"] };

  it("is true when both stage and domain match (or apply to all)", () => {
    const advice = loadAdvice(FIXTURES_DIR);
    const wildcard = getAdviceById(
      advice,
      "yc-youtube-sample-pricing-lesson--02",
    );
    expect(wildcard && matchesProfile(wildcard, profile)).toBe(true);
  });

  it("is false when neither stage nor domain matches", () => {
    const advice = loadAdvice(FIXTURES_DIR);
    const mismatch = getAdviceById(
      advice,
      "lightcone-sample-enterprise-first-customers--03",
    );
    expect(mismatch && matchesProfile(mismatch, profile)).toBe(false);
  });
});
