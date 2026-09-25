import fs from "node:fs";
import path from "node:path";

const ENV_LINE_PATTERN = /^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$/;

/**
 * Loads `KEY=VALUE` lines from the given `.env` file into `process.env`,
 * without overriding variables already set (e.g. by `.env.local` or the
 * shell). Silently does nothing when the file doesn't exist.
 */
export function loadRepoRootEnvFrom(filePath: string): void {
  if (!fs.existsSync(filePath)) return;
  const raw = fs.readFileSync(filePath, "utf-8");
  for (const line of raw.split("\n")) {
    if (line.trim().startsWith("#") || line.trim() === "") continue;
    const match = ENV_LINE_PATTERN.exec(line);
    if (!match) continue;
    const [, key, rawValue] = match;
    if (process.env[key] !== undefined) continue;
    process.env[key] = stripQuotes(rawValue.trim());
  }
}

/** Loads `ANTHROPIC_API_KEY` (and friends) from the repo-root `.env`. */
export function loadRepoRootEnv(): void {
  loadRepoRootEnvFrom(path.resolve(process.cwd(), "..", ".env"));
}

function stripQuotes(value: string): string {
  const isDoubleQuoted = value.startsWith('"') && value.endsWith('"');
  const isSingleQuoted = value.startsWith("'") && value.endsWith("'");
  if ((isDoubleQuoted || isSingleQuoted) && value.length >= 2) {
    return value.slice(1, -1);
  }
  return value;
}
