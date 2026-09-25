import {
  extractWikilinkSlugs,
  parseAdviceHref,
  resolveAdviceMarkers,
  resolveWikilinks,
  transformKeywordMarkdown,
} from "./markdown";

describe("extractWikilinkSlugs", () => {
  it("returns the unique set of referenced slugs", () => {
    expect(
      extractWikilinkSlugs("[[a]] 그리고 [[b]], 또 [[a]]"),
    ).toEqual(["a", "b"]);
  });

  it("returns an empty array when there are no wikilinks", () => {
    expect(extractWikilinkSlugs("일반 텍스트")).toEqual([]);
  });
});

describe("resolveWikilinks", () => {
  it("turns [[slug]] into a markdown link to /k/slug using the given title", () => {
    const titleFor = (slug: string) =>
      ({ pricing: "가격 책정" })[slug];
    expect(resolveWikilinks("보라: [[pricing]] 문서", titleFor)).toBe(
      "보라: [가격 책정](/k/pricing) 문서",
    );
  });

  it("falls back to the raw slug as the title when unknown", () => {
    const titleFor = () => undefined;
    expect(resolveWikilinks("[[unknown-slug]]", titleFor)).toBe(
      "[unknown-slug](/k/unknown-slug)",
    );
  });

  it("replaces multiple wikilinks", () => {
    const titleFor = (slug: string) =>
      ({ a: "A", b: "B" })[slug];
    expect(resolveWikilinks("[[a]] and [[b]]", titleFor)).toBe(
      "[A](/k/a) and [B](/k/b)",
    );
  });

  it("leaves normal markdown links untouched", () => {
    const titleFor = () => undefined;
    const text = "[일반 링크](https://example.com)";
    expect(resolveWikilinks(text, titleFor)).toBe(text);
  });
});

describe("resolveAdviceMarkers", () => {
  it("turns {{advice:id}} into a markdown link with an advice:// href", () => {
    const result = resolveAdviceMarkers("근거: {{advice:some-source--01}}.");
    expect(result).toContain("(advice://some-source--01)");
    expect(result).not.toContain("{{advice:");
  });

  it("replaces multiple advice markers", () => {
    const result = resolveAdviceMarkers(
      "{{advice:a--01}} 그리고 {{advice:b--02}}",
    );
    expect(result).toContain("(advice://a--01)");
    expect(result).toContain("(advice://b--02)");
  });
});

describe("parseAdviceHref", () => {
  it("extracts the advice id from an advice:// href", () => {
    expect(parseAdviceHref("advice://some-source--01")).toBe(
      "some-source--01",
    );
  });

  it("returns null for a non-advice href", () => {
    expect(parseAdviceHref("https://example.com")).toBeNull();
    expect(parseAdviceHref("/k/pricing")).toBeNull();
  });
});

describe("transformKeywordMarkdown", () => {
  it("applies both wikilink and advice-marker transforms", () => {
    const titleFor = (slug: string) => ({ pricing: "가격 책정" })[slug];
    const input = "[[pricing]] 참고. {{advice:x--01}}";
    const result = transformKeywordMarkdown(input, titleFor);
    expect(result).toContain("[가격 책정](/k/pricing)");
    expect(result).toContain("(advice://x--01)");
  });

  it("leaves mermaid code fences untouched", () => {
    const titleFor = () => undefined;
    const input = "```mermaid\nflowchart TD\n  A --> B\n```";
    expect(transformKeywordMarkdown(input, titleFor)).toBe(input);
  });
});
