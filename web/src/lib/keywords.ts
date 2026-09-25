import fs from "node:fs";
import path from "node:path";
import matter from "gray-matter";
import { z } from "zod";
import type { KeywordPage } from "./types";
import { yamlDateString } from "./yaml";

const imageSchema = z.object({
  src: z.string().min(1),
  alt: z.string().default(""),
  source: z.string().min(1),
});

const keywordFrontmatterSchema = z.object({
  slug: z.string().min(1),
  title: z.string().min(1),
  category: z.string().min(1),
  summary: z.string().min(1),
  reviewed: z.boolean().default(false),
  advice: z.array(z.string()).default([]),
  images: z.array(imageSchema).default([]),
  updated_at: yamlDateString,
});

function parseKeywordFile(filePath: string): KeywordPage {
  const raw = fs.readFileSync(filePath, "utf-8");
  const { data, content } = matter(raw);
  const result = keywordFrontmatterSchema.safeParse(data);
  if (!result.success) {
    throw new Error(
      `Invalid keyword frontmatter at ${filePath}: ${result.error.message}`,
    );
  }
  const fm = result.data;
  return {
    slug: fm.slug,
    title: fm.title,
    category: fm.category,
    summary: fm.summary,
    reviewed: fm.reviewed,
    advice: fm.advice,
    images: fm.images,
    updatedAt: fm.updated_at,
    body: content.trim(),
  };
}

/** Loads and validates every `keywords/{slug}.md` file. */
export function loadKeywordPages(contentDir: string): KeywordPage[] {
  const dir = path.join(contentDir, "keywords");
  if (!fs.existsSync(dir)) return [];
  return fs
    .readdirSync(dir)
    .filter((f) => f.endsWith(".md"))
    .map((f) => parseKeywordFile(path.join(dir, f)));
}

export function getKeywordBySlug(
  pages: readonly KeywordPage[],
  slug: string,
): KeywordPage | undefined {
  return pages.find((p) => p.slug === slug);
}
