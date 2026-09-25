import { buildEvidenceEntries, buildEvidenceLink, formatTimestamp } from "./evidence";
import type { Advice, Source } from "./types";

function makeSource(overrides: Partial<Source>): Source {
  return {
    id: "yc-youtube-sample-pricing-lesson",
    title: "How to Price",
    titleKo: "가격을 정하는 법",
    url: "https://example.com/sample/yc-pricing-lesson",
    origin: "yc-youtube",
    format: "video",
    youtubeId: "SAMPLE0001A",
    published: "2024-03-01",
    speakers: [],
    thumbnail: null,
    images: [],
    ingestedAt: "2026-09-25",
    summary: "요약",
    ...overrides,
  };
}

function makeAdvice(overrides: Partial<Advice>): Advice {
  return {
    id: "yc-youtube-sample-pricing-lesson--01",
    source: "yc-youtube-sample-pricing-lesson",
    category: "pricing",
    keywords: ["pricing-strategy"],
    context: { stage: [], domain: [] },
    speaker: null,
    claim: "가격을 높게 시작하라",
    anchor: { kind: "timestamp", start: 750 },
    matchScore: 96.5,
    body: "본문",
    ...overrides,
  };
}

describe("formatTimestamp", () => {
  it("formats 750 seconds as 12:30", () => {
    expect(formatTimestamp(750)).toBe("12:30");
  });

  it("pads seconds under 10", () => {
    expect(formatTimestamp(65)).toBe("1:05");
  });

  it("includes hours when past 3600 seconds", () => {
    expect(formatTimestamp(3725)).toBe("1:02:05");
  });
});

describe("buildEvidenceLink", () => {
  it("builds a YouTube timestamp link for a timestamp anchor", () => {
    const advice = makeAdvice({ anchor: { kind: "timestamp", start: 750 } });
    const source = makeSource({ youtubeId: "SAMPLE0001A" });
    const link = buildEvidenceLink(advice, source);
    expect(link.url).toBe(
      "https://www.youtube.com/watch?v=SAMPLE0001A&t=750s",
    );
    expect(link.label).toBe("12:30부터 보기");
  });

  it("falls back to the source URL when a timestamp advice has no youtubeId", () => {
    const advice = makeAdvice({ anchor: { kind: "timestamp", start: 45 } });
    const source = makeSource({ youtubeId: null, url: "https://example.com/x" });
    const link = buildEvidenceLink(advice, source);
    expect(link.url).toBe("https://example.com/x");
    expect(link.label).toBe("0:45부터 보기");
  });

  it("links a paragraph anchor to the source URL", () => {
    const advice = makeAdvice({ anchor: { kind: "paragraph", paragraph: 2 } });
    const source = makeSource({ url: "https://example.com/essay" });
    const link = buildEvidenceLink(advice, source);
    expect(link.url).toBe("https://example.com/essay");
    expect(link.label).toBe("원문에서 보기");
  });
});

describe("buildEvidenceEntries", () => {
  it("resolves advice ids into full evidence entries", () => {
    const advice = [makeAdvice({ id: "advice--01" })];
    const source = makeSource({});
    const entries = buildEvidenceEntries(["advice--01"], advice, [source]);
    expect(entries).toEqual([
      {
        adviceId: "advice--01",
        claim: "가격을 높게 시작하라",
        sourceTitle: "가격을 정하는 법",
        url: "https://www.youtube.com/watch?v=SAMPLE0001A&t=750s",
        label: "12:30부터 보기",
      },
    ]);
  });

  it("skips ids whose advice or source can't be found", () => {
    const entries = buildEvidenceEntries(["does-not-exist"], [], []);
    expect(entries).toEqual([]);
  });
});
