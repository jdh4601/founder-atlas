import { answerQuestion } from "./ask";
import type { AnthropicJsonClient } from "./anthropicClient";
import type { Advice, KeywordPage } from "./types";

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
    id: "yc-youtube-sample-pricing-lesson--01",
    source: "yc-youtube-sample-pricing-lesson",
    category: "pricing",
    keywords: ["pricing-strategy"],
    context: { stage: [], domain: [] },
    speaker: "Kevin Sample",
    claim: "가격을 높게 시작하라",
    anchor: { kind: "timestamp", start: 120 },
    matchScore: 96.5,
    body: "가격에 관한 본문 설명.",
    ...overrides,
  };
}

const keywordPages: KeywordPage[] = [
  makeKeywordPage({ slug: "pricing-strategy" }),
  makeKeywordPage({
    slug: "first-customers",
    category: "sales",
    summary: "첫 고객을 어떻게 확보할지에 대한 조언",
  }),
];

const advice: Advice[] = [
  makeAdvice({ id: "advice--01", keywords: ["pricing-strategy"] }),
  makeAdvice({
    id: "advice--02",
    keywords: ["first-customers"],
    claim: "첫 고객은 직접 확보하라",
  }),
];

function mockClient(
  responses: readonly unknown[],
): AnthropicJsonClient & { createJson: jest.Mock } {
  const createJson = jest.fn();
  for (const response of responses) createJson.mockResolvedValueOnce(response);
  return { createJson };
}

describe("answerQuestion", () => {
  it("returns a Korean answer citing advice ids when a keyword matches", async () => {
    const client = mockClient([
      { slugs: ["pricing-strategy"] },
      {
        answer: "초기에는 가격을 높게 시작하는 것이 좋습니다.",
        citedAdviceIds: ["advice--01"],
      },
    ]);

    const result = await answerQuestion(
      client,
      "가격을 어떻게 정해야 하나요?",
      keywordPages,
      advice,
    );

    expect(result.matched).toEqual(["pricing-strategy"]);
    expect(result.answered).toBe(true);
    expect(result.answer).toBe("초기에는 가격을 높게 시작하는 것이 좋습니다.");
    expect(result.citedAdvice).toEqual(["advice--01"]);
    expect(client.createJson).toHaveBeenCalledTimes(2);
  });

  it("returns answered: false and never calls step 2 when no keyword matches", async () => {
    const client = mockClient([{ slugs: [] }]);

    const result = await answerQuestion(
      client,
      "지분을 어떻게 나눠야 하나요?",
      keywordPages,
      advice,
    );

    expect(result.matched).toEqual([]);
    expect(result.answered).toBe(false);
    expect(result.answer).toBeNull();
    expect(result.citedAdvice).toEqual([]);
    expect(client.createJson).toHaveBeenCalledTimes(1);
  });

  it("drops matched slugs the model hallucinated that aren't real keyword pages", async () => {
    const client = mockClient([
      { slugs: ["not-a-real-slug", "pricing-strategy"] },
      { answer: "답변입니다.", citedAdviceIds: [] },
    ]);

    const result = await answerQuestion(
      client,
      "가격을 어떻게 정해야 하나요?",
      keywordPages,
      advice,
    );

    expect(result.matched).toEqual(["pricing-strategy"]);
  });

  it("drops cited advice ids that don't exist in the loaded advice", async () => {
    const client = mockClient([
      { slugs: ["pricing-strategy"] },
      {
        answer: "답변입니다.",
        citedAdviceIds: ["advice--01", "does-not-exist"],
      },
    ]);

    const result = await answerQuestion(
      client,
      "가격을 어떻게 정해야 하나요?",
      keywordPages,
      advice,
    );

    expect(result.citedAdvice).toEqual(["advice--01"]);
  });

  it("returns answered: false when step 1 returns null (unparseable response)", async () => {
    const client = mockClient([null]);

    const result = await answerQuestion(
      client,
      "가격을 어떻게 정해야 하나요?",
      keywordPages,
      advice,
    );

    expect(result.answered).toBe(false);
    expect(result.matched).toEqual([]);
  });

  it("returns answered: false when step 2 returns null (unparseable response)", async () => {
    const client = mockClient([{ slugs: ["pricing-strategy"] }, null]);

    const result = await answerQuestion(
      client,
      "가격을 어떻게 정해야 하나요?",
      keywordPages,
      advice,
    );

    expect(result.matched).toEqual(["pricing-strategy"]);
    expect(result.answered).toBe(false);
    expect(result.answer).toBeNull();
  });
});
