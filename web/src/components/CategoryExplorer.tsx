"use client";

import Link from "next/link";
import type { BrowseCategory } from "@/lib/sourceBrowse";

interface CategoryExplorerProps {
  readonly categories: readonly BrowseCategory[];
  /** `null` is the "전체" tab. */
  readonly categorySlug: string | null;
  readonly keywordSlug: string | null;
  readonly onSelectCategory: (slug: string | null) => void;
  readonly onSelectKeyword: (slug: string | null) => void;
}

const tabClass = "-mb-px flex items-center gap-2 border-b-2 px-3 py-2.5 text-[14px] transition-colors";

/** Category tabs and keyword chips that filter the content grid below. */
export function CategoryExplorer({
  categories,
  categorySlug,
  keywordSlug,
  onSelectCategory,
  onSelectKeyword,
}: CategoryExplorerProps) {
  const selected = categories.find((category) => category.slug === categorySlug) ?? null;
  const keyword = selected?.keywords.find((item) => item.slug === keywordSlug) ?? null;

  return (
    <div>
      <div className="no-scrollbar -mx-5 overflow-x-auto px-5 sm:mx-0 sm:px-0">
        <div role="tablist" aria-label="문제 범주" className="flex w-max gap-1 border-b border-line">
          <button
            type="button"
            role="tab"
            aria-selected={selected === null}
            onClick={() => onSelectCategory(null)}
            className={`${tabClass} ${selected === null ? "border-ink font-medium text-ink" : "border-transparent text-ink-muted hover:text-ink"}`}
          >
            전체
          </button>
          {categories.map((category) => {
            const isSelected = category.slug === selected?.slug;
            return (
              <button
                key={category.slug}
                type="button"
                role="tab"
                aria-selected={isSelected}
                onClick={() => onSelectCategory(category.slug)}
                className={`${tabClass} ${isSelected ? "font-medium text-ink" : "border-transparent text-ink-muted hover:text-ink"}`}
                style={isSelected ? { borderColor: category.color } : undefined}
              >
                <span aria-hidden className="h-2 w-2 rounded-full" style={{ backgroundColor: category.color }} />
                {category.title}
              </button>
            );
          })}
        </div>
      </div>

      {selected && (
        <div className="mt-4 flex flex-wrap items-center gap-2">
          {selected.keywords.map((item) => {
            const isPressed = item.slug === keywordSlug;
            return (
              <button
                key={item.slug}
                type="button"
                aria-pressed={isPressed}
                onClick={() => onSelectKeyword(isPressed ? null : item.slug)}
                className="rounded-full border px-3.5 py-1.5 text-[13.5px] transition-opacity hover:opacity-80"
                style={{
                  borderColor: `color-mix(in srgb, ${selected.color} ${isPressed ? 90 : 45}%, transparent)`,
                  backgroundColor: isPressed
                    ? selected.color
                    : `color-mix(in srgb, ${selected.color} 12%, var(--surface))`,
                  color: isPressed ? "var(--paper)" : `color-mix(in srgb, ${selected.color} 70%, var(--ink))`,
                }}
              >
                {item.title} <span className="ml-0.5 opacity-60">{item.count}</span>
              </button>
            );
          })}
          {keyword?.hasPage && (
            <Link href={`/k/${keyword.slug}`} className="ml-1 text-[13px] text-focus underline underline-offset-4">
              ‘{keyword.title}’ 키워드 페이지에서 조언 보기 →
            </Link>
          )}
        </div>
      )}
    </div>
  );
}
