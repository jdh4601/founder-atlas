import fs from "node:fs";
import path from "node:path";
import matter from "gray-matter";
import { z } from "zod";
import { DOMAINS, STAGES, type Advice } from "./types";

const anchorSchema = z.object({
  kind: z.enum(["timestamp", "paragraph"]),
  start: z.number().nullable().optional(),
  paragraph: z.number().nullable().optional(),
});

const adviceFrontmatterSchema = z.object({
  id: z.string().min(1),
  source: z.string().min(1),
  category: z.string().min(1),
  keywords: z.array(z.string().min(1)).min(1).max(3),
  context: z.object({
    stage: z.array(z.enum(STAGES)).default([]),
    domain: z.array(z.enum(DOMAINS)).default([]),
  }),
  speaker: z.string().nullable().optional(),
  claim: z.string().min(1),
  // `quote` is intentionally NOT in this schema: it is dropped by zod's
  // default "strip unknown keys" behavior, so it can never leak into the
  // `Advice` object the rest of the app (and the client) sees.
  anchor: anchorSchema,
  match_score: z.number().min(90),
});

function toAdviceAnchor(
  anchor: z.infer<typeof anchorSchema>,
  filePath: string,
): Advice["anchor"] {
  if (anchor.kind === "timestamp") {
    if (anchor.start == null) {
      throw new Error(`Timestamp anchor missing start at ${filePath}`);
    }
    return { kind: "timestamp", start: anchor.start };
  }
  if (anchor.paragraph == null) {
    throw new Error(`Paragraph anchor missing paragraph at ${filePath}`);
  }
  return { kind: "paragraph", paragraph: anchor.paragraph };
}

function parseAdviceFile(filePath: string): Advice {
  const raw = fs.readFileSync(filePath, "utf-8");
  const { data, content } = matter(raw);
  const result = adviceFrontmatterSchema.safeParse(data);
  if (!result.success) {
    throw new Error(
      `Invalid advice frontmatter at ${filePath}: ${result.error.message}`,
    );
  }
  const fm = result.data;
  return {
    id: fm.id,
    source: fm.source,
    category: fm.category,
    keywords: fm.keywords,
    context: fm.context,
    speaker: fm.speaker ?? null,
    claim: fm.claim,
    anchor: toAdviceAnchor(fm.anchor, filePath),
    matchScore: fm.match_score,
    body: content.trim(),
  };
}

/**
 * Loads and validates every `advice/{id}.md` file. The `quote` field is
 * never read into the returned objects — see the schema comment above.
 */
export function loadAdvice(contentDir: string): Advice[] {
  const dir = path.join(contentDir, "advice");
  if (!fs.existsSync(dir)) return [];
  return fs
    .readdirSync(dir)
    .filter((f) => f.endsWith(".md"))
    .map((f) => parseAdviceFile(path.join(dir, f)));
}

export function getAdviceById(
  advice: readonly Advice[],
  id: string,
): Advice | undefined {
  return advice.find((a) => a.id === id);
}

/** Returns advice for the given ids, in that order, skipping unknown ids. */
export function getAdviceByIds(
  advice: readonly Advice[],
  ids: readonly string[],
): Advice[] {
  const byId = new Map(advice.map((a) => [a.id, a] as const));
  return ids.flatMap((id) => {
    const found = byId.get(id);
    return found ? [found] : [];
  });
}

export function getAdviceForKeyword(
  advice: readonly Advice[],
  keywordSlug: string,
): Advice[] {
  return advice.filter((a) => a.keywords.includes(keywordSlug));
}
