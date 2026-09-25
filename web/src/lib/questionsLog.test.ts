import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { appendQuestionLog } from "./questionsLog";
import type { QuestionLogEntry } from "./types";

describe("appendQuestionLog", () => {
  let contentDir: string;

  beforeEach(() => {
    contentDir = fs.mkdtempSync(path.join(os.tmpdir(), "questions-log-test-"));
  });

  it("creates content/questions/log.jsonl and appends one JSON line", () => {
    const entry: QuestionLogEntry = {
      ts: "2026-09-25T10:00:00Z",
      question: "가격을 어떻게 정해야 하나요?",
      matched: ["pricing-strategy"],
      answered: true,
      answer: "짧은 답변입니다.",
      citedAdvice: ["yc-youtube-sample-pricing-lesson--01"],
      clicked: null,
    };

    appendQuestionLog(contentDir, entry);

    const logPath = path.join(contentDir, "questions", "log.jsonl");
    const lines = fs.readFileSync(logPath, "utf-8").trim().split("\n");
    expect(lines).toHaveLength(1);
    expect(JSON.parse(lines[0])).toEqual({
      ts: "2026-09-25T10:00:00Z",
      question: "가격을 어떻게 정해야 하나요?",
      matched: ["pricing-strategy"],
      answered: true,
      answer: "짧은 답변입니다.",
      cited_advice: ["yc-youtube-sample-pricing-lesson--01"],
      clicked: null,
    });
  });

  it("appends subsequent entries as new lines without truncating prior ones", () => {
    const first: QuestionLogEntry = {
      ts: "2026-09-25T10:00:00Z",
      question: "첫 질문",
      matched: [],
      answered: false,
      answer: null,
      citedAdvice: [],
      clicked: null,
    };
    const second: QuestionLogEntry = { ...first, question: "두번째 질문" };

    appendQuestionLog(contentDir, first);
    appendQuestionLog(contentDir, second);

    const logPath = path.join(contentDir, "questions", "log.jsonl");
    const lines = fs.readFileSync(logPath, "utf-8").trim().split("\n");
    expect(lines).toHaveLength(2);
    expect(JSON.parse(lines[1]).question).toBe("두번째 질문");
  });
});
