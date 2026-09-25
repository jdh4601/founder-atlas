import path from "node:path";

const DEFAULT_CONTENT_DIR = "../content";

/**
 * Resolves the directory that holds the repo's `content/` data.
 *
 * Defaults to `../content` (the repo-root `content/` directory, one level
 * up from `web/`). Override with `CONTENT_DIR` in `.env.local` — for local
 * development this points at `./__fixtures__/content` since the pipeline
 * has not produced real content yet.
 */
export function getContentDir(): string {
  const configured = process.env.CONTENT_DIR ?? DEFAULT_CONTENT_DIR;
  // `content/` lives outside `web/`'s own source tree (or is a fixtures
  // dir), so it must never be included in Turbopack's output file tracing.
  return path.resolve(/* turbopackIgnore: true */ process.cwd(), configured);
}
