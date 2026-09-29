import fs from "node:fs";
import path from "node:path";
import matter from "gray-matter";
import { z } from "zod";

const articleSchema = z.object({
  source: z.string().min(1),
  title_ko: z.string().min(1),
  tldr: z.string().default(""),
  lead: z.string().min(1),
  tags: z.array(z.string()).default([]),
  source_sha256: z.string().length(64),
  generated_at: z.string().min(1),
});

export interface SourceArticle {
  readonly titleKo: string;
  readonly tldr: string;
  readonly lead: string;
  readonly tags: readonly string[];
  readonly body: string;
}

export function loadSourceArticle(contentDir: string, sourceId: string): SourceArticle | null {
  if (!/^[a-z0-9-]+$/.test(sourceId)) return null;
  const file = path.join(contentDir, "source_articles", `${sourceId}.md`);
  if (!fs.existsSync(file)) return null;
  const { data, content } = matter(fs.readFileSync(file, "utf-8"));
  const parsed = articleSchema.safeParse(data);
  if (!parsed.success || parsed.data.source !== sourceId || !content.trim()) {
    throw new Error(`Invalid source article at ${file}`);
  }
  return {
    titleKo: parsed.data.title_ko,
    tldr: parsed.data.tldr,
    lead: parsed.data.lead,
    tags: parsed.data.tags,
    body: content.trim(),
  };
}
