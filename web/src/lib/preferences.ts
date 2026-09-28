"use client";

import { useSyncExternalStore } from "react";

import type { Theme } from "./preferenceKeys";

export { ASK_PROVIDERS, PREFERENCE_KEYS, THEMES } from "./preferenceKeys";
export type { AskProvider, Theme } from "./preferenceKeys";

const CHANGE_EVENT = "founder-atlas:preference-change";

export function readPreference<T extends string>(
  key: string,
  allowed: readonly T[],
  fallback: T,
): T {
  try {
    const stored = window.localStorage.getItem(key);
    return allowed.find((value) => value === stored) ?? fallback;
  } catch {
    return fallback;
  }
}

export function writePreference(key: string, value: string): void {
  try {
    window.localStorage.setItem(key, value);
  } catch (error) {
    console.warn(`[preferences] could not save ${key}; keeping it for this page only`, error);
  }
  window.dispatchEvent(new Event(CHANGE_EVENT));
}

function subscribe(onChange: () => void): () => void {
  window.addEventListener(CHANGE_EVENT, onChange);
  window.addEventListener("storage", onChange);
  return () => {
    window.removeEventListener(CHANGE_EVENT, onChange);
    window.removeEventListener("storage", onChange);
  };
}

export function usePreference<T extends string>(
  key: string,
  allowed: readonly T[],
  fallback: T,
): T {
  return useSyncExternalStore(
    subscribe,
    () => readPreference(key, allowed, fallback),
    () => fallback,
  );
}

/** `system` removes the attribute so the OS color scheme applies. */
export function applyTheme(theme: Theme): void {
  const root = document.documentElement;
  if (theme === "system") delete root.dataset.theme;
  else root.dataset.theme = theme;
}
