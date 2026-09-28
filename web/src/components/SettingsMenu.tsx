"use client";

import { useEffect, useRef, useState } from "react";
import {
  ASK_PROVIDERS,
  PREFERENCE_KEYS,
  THEMES,
  applyTheme,
  usePreference,
  writePreference,
  type AskProvider,
  type Theme,
} from "@/lib/preferences";

const THEME_LABELS: Record<Theme, string> = {
  system: "시스템",
  light: "라이트",
  dark: "다크",
};

const PROVIDER_LABELS: Record<AskProvider, string> = {
  anthropic: "Anthropic API (API 키 필요)",
  "codex-cli": "Codex CLI (로컬 서버)",
  "claude-code-cli": "Claude Code CLI (로컬 서버)",
};

/** Header gear menu: color theme and the model used by the ask box. */
export function SettingsMenu() {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const theme = usePreference(PREFERENCE_KEYS.theme, THEMES, "system");
  const provider = usePreference(PREFERENCE_KEYS.askProvider, ASK_PROVIDERS, "anthropic");

  useEffect(() => {
    if (!isOpen) return;
    function closeOnOutside(event: MouseEvent): void {
      if (!containerRef.current?.contains(event.target as Node)) setIsOpen(false);
    }
    function closeOnEscape(event: KeyboardEvent): void {
      if (event.key === "Escape") setIsOpen(false);
    }
    document.addEventListener("mousedown", closeOnOutside);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("mousedown", closeOnOutside);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [isOpen]);

  function selectTheme(next: Theme): void {
    writePreference(PREFERENCE_KEYS.theme, next);
    applyTheme(next);
  }

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        aria-label="설정"
        aria-expanded={isOpen}
        onClick={() => setIsOpen((open) => !open)}
        className="flex h-9 w-9 items-center justify-center rounded-lg text-ink-muted transition-colors hover:bg-surface hover:text-ink"
      >
        <GearIcon />
      </button>

      {isOpen && (
        <div className="absolute right-0 top-11 z-20 w-[280px] max-w-[calc(100vw-40px)] rounded-xl border border-line bg-surface p-4 shadow-lg">
          <fieldset>
            <legend className="text-[12.5px] font-medium text-ink-muted">화면 모드</legend>
            <div className="mt-2 grid grid-cols-3 gap-1 rounded-lg bg-paper p-1">
              {THEMES.map((value) => (
                <label
                  key={value}
                  className={`cursor-pointer rounded-md py-1.5 text-center text-[13px] transition-colors ${theme === value ? "bg-surface font-medium text-ink shadow-sm" : "text-ink-muted hover:text-ink"}`}
                >
                  <input
                    type="radio"
                    name="theme"
                    value={value}
                    checked={theme === value}
                    onChange={() => selectTheme(value)}
                    className="sr-only"
                  />
                  {THEME_LABELS[value]}
                </label>
              ))}
            </div>
          </fieldset>

          <label htmlFor="ask-provider" className="mt-4 block text-[12.5px] font-medium text-ink-muted">
            응답 모델
          </label>
          <select
            id="ask-provider"
            value={provider}
            onChange={(event) => writePreference(PREFERENCE_KEYS.askProvider, event.target.value)}
            className="mt-2 w-full rounded-lg border border-line bg-paper px-2.5 py-2 text-[13px] text-ink focus:border-focus"
          >
            {ASK_PROVIDERS.map((value) => (
              <option key={value} value={value}>
                {PROVIDER_LABELS[value]}
              </option>
            ))}
          </select>
          {provider !== "anthropic" && (
            <p className="mt-2 text-[12px] leading-relaxed text-ink-muted">
              CLI 연결은 해당 CLI가 설치되고 인증된 로컬 서버에서만 사용할 수 있어요.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function GearIcon() {
  return (
    <svg aria-hidden width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
  );
}
