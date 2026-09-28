/**
 * Per-browser UI preferences kept in localStorage. Storage can be
 * unavailable (private mode, blocked site data), so every access falls
 * back to the default instead of failing the page.
 */
export const PREFERENCE_KEYS = {
  theme: "founder-atlas:theme",
  askProvider: "founder-atlas:ask-provider",
} as const;

export const THEMES = ["system", "light", "dark"] as const;
export type Theme = (typeof THEMES)[number];

export const ASK_PROVIDERS = ["anthropic", "codex-cli", "claude-code-cli"] as const;
export type AskProvider = (typeof ASK_PROVIDERS)[number];

/** Inline script for <head>: applies the saved theme before first paint. */
export const THEME_BOOT_SCRIPT = `try{var t=localStorage.getItem(${JSON.stringify(
  PREFERENCE_KEYS.theme,
)});if(t==="light"||t==="dark")document.documentElement.dataset.theme=t}catch(e){}`;
