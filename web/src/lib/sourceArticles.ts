import fs from "node:fs";
import path from "node:path";
import matter from "gray-matter";
import { z } from "zod";

const articleSchema = z.object({
  source: z.string().min(1),
  title_ko: z.string().min(1),
  lead: z.string().min(1),
  source_sha256: z.string().length(64),
  generated_at: z.string().min(1),
  reviewed: z.boolean(),
});

export interface SourceArticle {
  readonly titleKo: string;
  readonly lead: string;
  readonly body: string;
  readonly reviewed: boolean;
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
    lead: parsed.data.lead,
    body: content.trim(),
    reviewed: parsed.data.reviewed,
  };
}
