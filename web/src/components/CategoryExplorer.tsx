"use client";

import { useState } from "react";
import Link from "next/link";
import type { TaxonomyCategory } from "@/lib/types";

export type CategoryGroup = TaxonomyCategory;

interface CategoryExplorerProps {
  /** Categories already trimmed to keywords that have a page. */
  readonly groups: readonly CategoryGroup[];
}

/** Category tabs; the selected tab shows its keyword chips linking to `/k/[slug]`. */
export function CategoryExplorer({ groups }: CategoryExplorerProps) {
  const [selectedSlug, setSelectedSlug] = useState(groups[0]?.slug);
  const selected = groups.find((group) => group.slug === selectedSlug) ?? groups[0];
  if (!selected) return null;

  return (
    <div>
      <div className="no-scrollbar -mx-5 overflow-x-auto px-5 sm:mx-0 sm:px-0">
        <div role="tablist" aria-label="문제 범주" className="flex w-max gap-1 border-b border-line">
          {groups.map((group) => {
            const isSelected = group.slug === selected.slug;
            return (
              <button
                key={group.slug}
                type="button"
                role="tab"
                id={`category-tab-${group.slug}`}
                aria-selected={isSelected}
                aria-controls="category-keywords"
                onClick={() => setSelectedSlug(group.slug)}
                className={`-mb-px flex items-center gap-2 border-b-2 px-3 py-2.5 text-[14px] transition-colors ${isSelected ? "font-medium text-ink" : "border-transparent text-ink-muted hover:text-ink"}`}
                style={isSelected ? { borderColor: group.color } : undefined}
              >
                <span aria-hidden className="h-2 w-2 rounded-full" style={{ backgroundColor: group.color }} />
                {group.title}
              </button>
            );
          })}
        </div>
      </div>

      <ul
        id="category-keywords"
        role="tabpanel"
        aria-labelledby={`category-tab-${selected.slug}`}
        className="mt-4 flex flex-wrap gap-2"
      >
        {selected.keywords.map((keyword) => (
          <li key={keyword.slug}>
            <Link
              href={`/k/${keyword.slug}`}
              className="inline-block rounded-full border px-3.5 py-1.5 text-[13.5px] transition-opacity hover:opacity-80"
              style={{
                borderColor: `color-mix(in srgb, ${selected.color} 45%, transparent)`,
                backgroundColor: `color-mix(in srgb, ${selected.color} 12%, var(--surface))`,
                color: `color-mix(in srgb, ${selected.color} 70%, var(--ink))`,
              }}
            >
              {keyword.title}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
