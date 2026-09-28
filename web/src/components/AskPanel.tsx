"use client";

import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { AskResults, type AskResultData } from "./AskResults";
import { SHOW_BROWSE_EVENT } from "./BrowseNavLink";
import { ASK_PROVIDERS, PREFERENCE_KEYS, readPreference } from "@/lib/preferences";

const DEFAULT_ERROR = "질문을 처리하지 못했어요. 잠시 후 다시 시도해 주세요.";
const CLI_UNAVAILABLE_ERROR =
  "이 CLI를 사용할 수 없어요. 로컬 서버에 CLI가 설치되고 로그인되어 있는지 확인해 주세요.";

interface AskPanelProps {
  /** Browse content (categories, content grid) hidden while a question is active. */
  readonly children?: ReactNode;
  /** Keyword page slug: answers come only from that keyword's advice. */
  readonly keyword?: string;
  readonly placeholder?: string;
}

type AskStatus = "idle" | "loading" | "answered" | "error";

/** Question input plus its answer view, which temporarily replaces `children`. */
export function AskPanel({
  children,
  keyword,
  placeholder = "예: 첫 엔터프라이즈 고객 가격을 어떻게 잡아야 할지 모르겠어요",
}: AskPanelProps) {
  const [question, setQuestion] = useState("");
  const [status, setStatus] = useState<AskStatus>("idle");
  const [errorMessage, setErrorMessage] = useState(DEFAULT_ERROR);
  const [result, setResult] = useState<AskResultData | null>(null);

  useEffect(() => {
    if (!children) return;
    function showBrowse(): void {
      setStatus("idle");
      setResult(null);
    }
    window.addEventListener(SHOW_BROWSE_EVENT, showBrowse);
    return () => window.removeEventListener(SHOW_BROWSE_EVENT, showBrowse);
  }, [children]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || status === "loading") return;

    const provider = readPreference(PREFERENCE_KEYS.askProvider, ASK_PROVIDERS, "anthropic");
    setStatus("loading");
    setResult(null);
    setErrorMessage(DEFAULT_ERROR);
    try {
      const response = await fetch("/api/ask", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ question: trimmed, provider, ...(keyword && { keyword }) }),
      });
      if (!response.ok) {
        if (response.status === 503 && provider !== "anthropic") {
          setErrorMessage(CLI_UNAVAILABLE_ERROR);
        }
        throw new Error(`ask request failed with status ${response.status}`);
      }
      setResult((await response.json()) as AskResultData);
      setStatus("answered");
    } catch (error) {
      console.warn("[AskPanel] question failed", error);
      setStatus("error");
    }
  }

  function reset(): void {
    setStatus("idle");
    setResult(null);
  }

  const isActive = status !== "idle";

  return (
    <div>
      <form onSubmit={handleSubmit} className="flex flex-col gap-3 sm:flex-row">
        <input
          name="question"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder={placeholder}
          aria-label="지금 어떤 문제에 부딪혔나요?"
          className="w-full rounded-lg border border-line bg-surface px-4 py-3.5 text-[15px] text-ink placeholder:text-ink-muted focus:border-focus"
        />
        <button
          type="submit"
          disabled={status === "loading"}
          className="shrink-0 rounded-lg bg-focus px-5 py-3.5 text-[15px] font-medium text-paper transition-opacity hover:opacity-90 disabled:opacity-60"
        >
          {status === "loading" ? "찾는 중..." : "물어보기"}
        </button>
      </form>

      {isActive ? (
        <section aria-live="polite" className="mt-8">
          <button
            type="button"
            onClick={reset}
            disabled={status === "loading"}
            className="text-[13.5px] text-ink-muted transition-colors hover:text-ink disabled:opacity-50"
          >
            ← {children ? "둘러보기로 돌아가기" : "답변 닫기"}
          </button>
          {status === "loading" && <AnswerSkeleton />}
          {status === "error" && (
            <p className="mt-4 rounded-lg border border-line bg-surface px-4 py-3.5 text-[14px] text-ink-muted">
              {errorMessage}
            </p>
          )}
          {result && <AskResults result={result} />}
        </section>
      ) : (
        children
      )}
    </div>
  );
}

function AnswerSkeleton() {
  return (
    <div className="mt-6 space-y-3" aria-label="관련 조언을 찾는 중">
      <p className="text-[14px] text-ink-muted">관련 조언을 찾고 있어요…</p>
      <div className="h-20 animate-pulse rounded-lg bg-surface" />
      <div className="h-14 animate-pulse rounded-lg bg-surface" />
    </div>
  );
}
