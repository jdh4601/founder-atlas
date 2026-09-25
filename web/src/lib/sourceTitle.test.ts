import { toKoreanSourceTitle } from "./sourceTitle";

it("uses an explicitly translated title first", () => {
  expect(toKoreanSourceTitle("Any English title", "직접 번역한 제목")).toBe("직접 번역한 제목");
});

it("translates the common explore titles", () => {
  expect(toKoreanSourceTitle("How to Get Your First 10 Customers")).toBe("첫 고객 10명 확보하는 법");
});

it("never falls back to an English title", () => {
  expect(toKoreanSourceTitle("An Untranslated Startup Article", "", "a16z-startup-article")).toMatch(/[가-힣]/);
});
