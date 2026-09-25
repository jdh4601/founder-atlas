import fs from "node:fs";
import path from "node:path";
import matter from "gray-matter";
import { z } from "zod";
import { ORIGINS, SOURCE_FORMATS, type Source } from "./types";
import { yamlDateString } from "./yaml";

const sourceFrontmatterSchema = z.object({
  id: z.string().min(1),
  title: z.string().min(1),
  // Empty until a Korean title is written; ingest runs without an API key.
  title_ko: z.string().default(""),
  url: z.string().min(1),
  origin: z.enum(ORIGINS),
  format: z.enum(SOURCE_FORMATS),
  youtube_id: z.string().nullable().optional(),
  published: yamlDateString.nullable().optional(),
  speakers: z.array(z.string()).default([]),
  thumbnail: z.string().nullable().optional(),
  images: z.array(z.string()).default([]),
  ingested_at: yamlDateString,
});

function parseSourceFile(filePath: string): Source {
  const raw = fs.readFileSync(filePath, "utf-8");
  const { data, content } = matter(raw);
  const result = sourceFrontmatterSchema.safeParse(data);
  if (!result.success) {
    throw new Error(
      `Invalid source frontmatter at ${filePath}: ${result.error.message}`,
    );
  }
  const fm = result.data;
  return {
    id: fm.id,
    title: fm.title,
    titleKo: fm.title_ko || fm.title,
    url: fm.url,
    origin: fm.origin,
    format: fm.format,
    youtubeId: fm.youtube_id ?? null,
    published: fm.published ?? null,
    speakers: fm.speakers,
    thumbnail: fm.thumbnail ?? null,
    images: fm.images,
    ingestedAt: fm.ingested_at,
    summary: content.trim(),
  };
}

/** Loads and validates every `sources/{id}.md` file. Skips transcript JSON. */
export function loadSources(contentDir: string): Source[] {
  const dir = path.join(contentDir, "sources");
  if (!fs.existsSync(dir)) return [];
  return fs
    .readdirSync(dir)
    .filter((f) => f.endsWith(".md"))
    .map((f) => parseSourceFile(path.join(dir, f)));
}

export function getSourceById(
  sources: readonly Source[],
  id: string,
): Source | undefined {
  return sources.find((s) => s.id === id);
}
