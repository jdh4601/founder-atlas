import Link from "next/link";
import type { KeywordPage, Taxonomy } from "@/lib/types";

interface CategoryExplorerProps {
  readonly taxonomy: Taxonomy;
  readonly keywordPages: readonly KeywordPage[];
}

/** The 8 fixed categories, each showing only the keywords that have a page. */
export function CategoryExplorer({ taxonomy, keywordPages }: CategoryExplorerProps) {
  const pageSlugs = new Set(keywordPages.map((page) => page.slug));

  return (
    <div className="grid gap-x-10 gap-y-8 sm:grid-cols-2">
      {taxonomy.categories.map((category) => {
        const keywords = category.keywords.filter((k) => pageSlugs.has(k.slug));
        if (keywords.length === 0) return null;
        return (
          <section key={category.slug}>
            <h3 className="flex items-center gap-2 text-[14px] font-medium text-ink">
              <span
                aria-hidden
                className="h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: category.color }}
              />
              {category.title}
            </h3>
            <ul className="mt-2.5 flex flex-wrap gap-2">
              {keywords.map((keyword) => (
                <li key={keyword.slug}>
                  <Link
                    href={`/k/${keyword.slug}`}
                    className="inline-block rounded-full border px-3 py-1.5 text-[13.5px] transition-colors"
                    style={{
                      borderColor: `color-mix(in srgb, ${category.color} 45%, transparent)`,
                      backgroundColor: `color-mix(in srgb, ${category.color} 12%, var(--surface))`,
                      color: `color-mix(in srgb, ${category.color} 70%, var(--ink))`,
                    }}
                  >
                    {keyword.title}
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        );
      })}
    </div>
  );
}
