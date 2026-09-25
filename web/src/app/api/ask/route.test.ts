import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const FIXTURES_DIR = path.join(__dirname, "../../../../__fixtures__/content");

jest.mock("../../../lib/anthropicClient", () => ({
  createAnthropicJsonClient: jest.fn(),
}));

import { createAnthropicJsonClient } from "../../../lib/anthropicClient";
import { POST } from "./route";

function makeRequest(body: unknown): Request {
  return new Request("http://localhost/api/ask", {
    method: "POST",
    body: JSON.stringify(body),
    headers: { "content-type": "application/json" },
  });
}

describe("POST /api/ask", () => {
  const originalEnv = { ...process.env };
  let contentDir: string;

  beforeEach(() => {
    jest.clearAllMocks();
    contentDir = fs.mkdtempSync(path.join(os.tmpdir(), "ask-route-test-"));
    fs.cpSync(FIXTURES_DIR, contentDir, { recursive: true });
    process.env.CONTENT_DIR = contentDir;
  });

  afterEach(() => {
    process.env = { ...originalEnv };
  });

  it("returns a clear 500 when ANTHROPIC_API_KEY is missing", async () => {
    delete process.env.ANTHROPIC_API_KEY;

    const response = await POST(makeRequest({ question: "질문" }));

    expect(response.status).toBe(500);
    const body = await response.json();
    expect(body.error).toMatch(/ANTHROPIC_API_KEY/);
    expect(createAnthropicJsonClient).not.toHaveBeenCalled();
  });

  it("answers, then appends the question to content/questions/log.jsonl", async () => {
    process.env.ANTHROPIC_API_KEY = "sk-test-key";
    const createJson = jest
      .fn()
      .mockResolvedValueOnce({ slugs: ["pricing-strategy"] })
      .mockResolvedValueOnce({
        answer: "가격을 높게 시작하는 것이 좋습니다.",
        citedAdviceIds: ["yc-youtube-sample-pricing-lesson--01"],
      });
    (createAnthropicJsonClient as jest.Mock).mockReturnValue({ createJson });

    const response = await POST(
      makeRequest({ question: "가격을 어떻게 정해야 하나요?" }),
    );

    expect(response.status).toBe(200);
    const body = await response.json();
    expect(body.answered).toBe(true);
    expect(body.matchedPages).toEqual([
      {
        slug: "pricing-strategy",
        title: "가격 책정",
        summary: "초기 제품의 가격을 얼마로, 어떻게 정할지에 대한 조언 모음",
      },
    ]);
    expect(body.evidence).toEqual([
      {
        adviceId: "yc-youtube-sample-pricing-lesson--01",
        claim: "초기 B2B 제품은 가격을 낮추지 말고 높게 시작하라",
        sourceTitle: "제품 가격을 정하는 법 (샘플)",
        url: "https://www.youtube.com/watch?v=SAMPLE0001A&t=120s",
        label: "2:00부터 보기",
      },
    ]);

    const logPath = path.join(contentDir, "questions", "log.jsonl");
    const lines = fs.readFileSync(logPath, "utf-8").trim().split("\n");
    const lastEntry = JSON.parse(lines[lines.length - 1]);
    expect(lastEntry.question).toBe("가격을 어떻게 정해야 하나요?");
    expect(lastEntry.answered).toBe(true);
    expect(lastEntry.cited_advice).toEqual([
      "yc-youtube-sample-pricing-lesson--01",
    ]);
  });

  it("returns 400 when the question is missing", async () => {
    process.env.ANTHROPIC_API_KEY = "sk-test-key";

    const response = await POST(makeRequest({}));

    expect(response.status).toBe(400);
  });
});
