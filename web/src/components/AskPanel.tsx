"use client";

import { useState, type FormEvent } from "react";
import { AskResults, type AskResultData } from "./AskResults";

/** The large question input on `/`, plus its result panel. */
export function AskPanel() {
  const [question, setQuestion] = useState("");
  const [provider, setProvider] = useState<
    "anthropic" | "codex-cli" | "claude-code-cli"
  >("anthropic");
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState(
    "질문을 처리하지 못했어요. 잠시 후 다시 시도해 주세요.",
  );
  const [result, setResult] = useState<AskResultData | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || status === "loading") return;

    setStatus("loading");
    setResult(null);
    setErrorMessage("질문을 처리하지 못했어요. 잠시 후 다시 시도해 주세요.");
    try {
      const response = await fetch("/api/ask", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ question: trimmed, provider }),
      });
      if (!response.ok) {
        if (response.status === 503 && provider !== "anthropic") {
          setErrorMessage(
            "이 CLI를 사용할 수 없어요. 로컬 서버에 CLI가 설치되고 로그인되어 있는지 확인해 주세요.",
          );
        }
        throw new Error("request failed");
      }
      const data = (await response.json()) as AskResultData;
      setResult(data);
      setStatus("idle");
    } catch {
      setStatus("error");
    }
  }

  return (
    <div>
      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <div className="flex flex-col gap-3 sm:flex-row">
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
        </div>
        <div className="flex flex-col gap-1.5">
          <label htmlFor="ask-provider" className="text-[13px] text-ink-muted">
            응답 모델 연결
          </label>
          <select
            id="ask-provider"
            name="provider"
            value={provider}
            onChange={(event) => setProvider(event.target.value as typeof provider)}
            disabled={status === "loading"}
            className="w-full rounded-lg border border-line bg-surface px-3 py-2 text-[14px] text-ink focus:border-focus sm:w-auto"
          >
            <option value="anthropic">Anthropic API (API 키 필요)</option>
            <option value="codex-cli">Codex CLI (로컬 서버)</option>
            <option value="claude-code-cli">Claude Code CLI (로컬 서버)</option>
          </select>
          {provider !== "anthropic" && (
            <p className="text-[12px] text-ink-muted">
              CLI 연결은 해당 CLI가 설치되고 인증된 로컬 서버에서만 사용할 수 있어요.
            </p>
          )}
        </div>
      </form>

      {status === "error" && (
        <p className="mt-3 text-[13.5px] text-ink-muted">
          {errorMessage}
        </p>
      )}

      {result && <AskResults result={result} />}
    </div>
  );
}
