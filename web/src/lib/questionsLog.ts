import fs from "node:fs";
import path from "node:path";
import type { QuestionLogEntry } from "./types";

/**
 * Appends one question to `content/questions/log.jsonl`, per
 * `docs/content-schema.md`. Creates the `questions/` directory and the log
 * file if they don't exist yet.
 */
export function appendQuestionLog(
  contentDir: string,
  entry: QuestionLogEntry,
): void {
  const dir = path.join(contentDir, "questions");
  fs.mkdirSync(dir, { recursive: true });
  const filePath = path.join(dir, "log.jsonl");
  const line = JSON.stringify(toLogRecord(entry));
  fs.appendFileSync(filePath, `${line}\n`, "utf-8");
}

function toLogRecord(entry: QuestionLogEntry): Record<string, unknown> {
  return {
    ts: entry.ts,
    question: entry.question,
    matched: entry.matched,
    answered: entry.answered,
    answer: entry.answer,
    cited_advice: entry.citedAdvice,
    clicked: entry.clicked,
  };
}
