import fs from "node:fs";
import path from "node:path";
import YAML from "js-yaml";
import { z } from "zod";
import type { Taxonomy, TaxonomyCategory } from "./types";

const keywordSchema = z.object({
  slug: z.string().min(1),
  title: z.string().min(1),
});

const categorySchema = z.object({
  slug: z.string().min(1),
  title: z.string().min(1),
  color: z.string().regex(/^#[0-9A-Fa-f]{6}$/, "color must be a hex string"),
  keywords: z.array(keywordSchema).max(20),
});

const taxonomySchema = z.object({
  categories: z.array(categorySchema).length(8),
});

/** Loads and validates `taxonomy.yaml` from the given content directory. */
export function loadTaxonomy(contentDir: string): Taxonomy {
  const filePath = path.join(contentDir, "taxonomy.yaml");
  const raw = fs.readFileSync(filePath, "utf-8");
  const parsed = YAML.load(raw);
  const result = taxonomySchema.safeParse(parsed);
  if (!result.success) {
    throw new Error(
      `Invalid taxonomy.yaml at ${filePath}: ${result.error.message}`,
    );
  }
  return result.data;
}

export function findCategory(
  taxonomy: Taxonomy,
  categorySlug: string,
): TaxonomyCategory | undefined {
  return taxonomy.categories.find((c) => c.slug === categorySlug);
}

export function findKeywordTitle(
  taxonomy: Taxonomy,
  keywordSlug: string,
): string | undefined {
  for (const category of taxonomy.categories) {
    const keyword = category.keywords.find((k) => k.slug === keywordSlug);
    if (keyword) return keyword.title;
  }
  return undefined;
}

/** Returns the category that owns the given keyword slug, if any. */
export function findCategoryForKeyword(
  taxonomy: Taxonomy,
  keywordSlug: string,
): TaxonomyCategory | undefined {
  return taxonomy.categories.find((category) =>
    category.keywords.some((k) => k.slug === keywordSlug),
  );
}
