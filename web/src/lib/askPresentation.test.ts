import { buildAskResponse } from "./askPresentation";
import type { AskResult } from "./ask";
import type { Advice, KeywordPage, Source } from "./types";

function makeKeywordPage(overrides: Partial<KeywordPage>): KeywordPage {
  return {
    slug: "pricing-strategy",
    title: "가격 책정",
    category: "pricing",
    summary: "초기 제품의 가격을 얼마로 정할지에 대한 조언",
    reviewed: true,
    advice: [],
    images: [],
    updatedAt: "2026-09-25",
    body: "",
    ...overrides,
  };
}

function makeAdvice(overrides: Partial<Advice>): Advice {
  return {
    id: "advice--01",
    source: "source-01",
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

function makeSource(overrides: Partial<Source>): Source {
  return {
    id: "source-01",
    title: "How to Price",
    titleKo: "가격을 정하는 법",
    url: "https://example.com/source-01",
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

describe("buildAskResponse", () => {
  const keywordPages = [makeKeywordPage({})];
  const advice = [makeAdvice({})];
  const sources = [makeSource({})];

  it("denormalizes matched slugs into keyword page summaries", () => {
    const result: AskResult = {
      matched: ["pricing-strategy"],
      answered: true,
      answer: "답변",
      citedAdvice: [],
    };
    const response = buildAskResponse(result, keywordPages, advice, sources);
    expect(response.matchedPages).toEqual([
      {
        slug: "pricing-strategy",
        title: "가격 책정",
        summary: "초기 제품의 가격을 얼마로 정할지에 대한 조언",
      },
    ]);
  });

  it("denormalizes cited advice ids into evidence with a claim, source title, and link", () => {
    const result: AskResult = {
      matched: ["pricing-strategy"],
      answered: true,
      answer: "답변",
      citedAdvice: ["advice--01"],
    };
    const response = buildAskResponse(result, keywordPages, advice, sources);
    expect(response.evidence).toEqual([
      {
        adviceId: "advice--01",
        claim: "가격을 높게 시작하라",
        sourceTitle: "가격을 정하는 법",
        url: "https://www.youtube.com/watch?v=SAMPLE0001A&t=750s",
        label: "12:30부터 보기",
      },
    ]);
  });

  it("skips a cited advice id whose advice or source can't be found", () => {
    const result: AskResult = {
      matched: [],
      answered: true,
      answer: "답변",
      citedAdvice: ["does-not-exist"],
    };
    const response = buildAskResponse(result, keywordPages, advice, sources);
    expect(response.evidence).toEqual([]);
  });

  it("carries answered/answer through unchanged", () => {
    const result: AskResult = {
      matched: [],
      answered: false,
      answer: null,
      citedAdvice: [],
    };
    const response = buildAskResponse(result, keywordPages, advice, sources);
    expect(response.answered).toBe(false);
    expect(response.answer).toBeNull();
  });
});
