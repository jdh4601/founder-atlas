"use client";

import { useState, type FormEvent } from "react";
import { AskResults, type AskResultData } from "./AskResults";

/** The large question input on `/`, plus its result panel. */
export function AskPanel() {
  const [question, setQuestion] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");
  const [result, setResult] = useState<AskResultData | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || status === "loading") return;

    setStatus("loading");
    setResult(null);
    try {
      const response = await fetch("/api/ask", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ question: trimmed }),
      });
      if (!response.ok) throw new Error("request failed");
      const data = (await response.json()) as AskResultData;
      setResult(data);
      setStatus("idle");
    } catch {
      setStatus("error");
    }
  }

  return (
    <div>
      <form onSubmit={handleSubmit} className="flex flex-col gap-3 sm:flex-row">
        <input
          name="question"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="예: 첫 엔터프라이즈 고객 가격을 어떻게 잡아야 할지 모르겠어요"
          aria-label="지금 어떤 문제에 부딪혔나요?"
          className="w-full rounded-lg border border-line bg-surface px-4 py-3.5 text-[15px] text-ink placeholder:text-ink-muted focus:border-focus"
        />
        <button
          type="submit"
          disabled={status === "loading"}
          className="shrink-0 rounded-lg bg-focus px-5 py-3.5 text-[15px] font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-60"
        >
          {status === "loading" ? "찾는 중..." : "물어보기"}
        </button>
      </form>

      {status === "error" && (
        <p className="mt-3 text-[13.5px] text-ink-muted">
          질문을 처리하지 못했어요. 잠시 후 다시 시도해 주세요.
        </p>
      )}

      {result && <AskResults result={result} />}
    </div>
  );
}
