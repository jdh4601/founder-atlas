"use client";

import { useMemo, useState } from "react";

import { CategoryExplorer } from "@/components/CategoryExplorer";
import { SourceBrowser } from "@/components/SourceBrowser";
import type { BrowseCategory, BrowseSource } from "@/lib/sourceBrowse";

interface ContentExplorerProps {
  readonly categories: readonly BrowseCategory[];
  readonly sources: readonly BrowseSource[];
}

/** Home browse area: category/keyword selection narrows the content grid below it. */
export function ContentExplorer({ categories, sources }: ContentExplorerProps) {
  const [categorySlug, setCategorySlug] = useState<string | null>(null);
  const [keywordSlug, setKeywordSlug] = useState<string | null>(null);
  const category = categories.find((item) => item.slug === categorySlug) ?? null;
  const keyword = category?.keywords.find((item) => item.slug === keywordSlug) ?? null;

  const visible = useMemo(() => {
    if (keyword) return sources.filter((source) => source.tags.some((tag) => tag.slug === keyword.slug));
    if (!category) return sources;
    const slugs = new Set(category.keywords.map((item) => item.slug));
    return sources.filter((source) => source.tags.some((tag) => slugs.has(tag.slug)));
  }, [sources, category, keyword]);

  function selectCategory(slug: string | null) {
    setCategorySlug(slug);
    setKeywordSlug(null);
  }

  return (
    <>
      <section id="keywords" className="mt-12 scroll-mt-20">
        <h2 className="text-[18px] font-semibold tracking-tight text-ink">범주별 키워드</h2>
        <div className="mt-3">
          <CategoryExplorer
            categories={categories}
            categorySlug={categorySlug}
            keywordSlug={keywordSlug}
            onSelectCategory={selectCategory}
            onSelectKeyword={setKeywordSlug}
          />
        </div>
      </section>
      <section id="contents" className="mt-14 scroll-mt-20">
        <SourceBrowser
          sources={visible}
          total={sources.length}
          filterLabel={keyword?.title ?? category?.title ?? null}
        />
      </section>
    </>
  );
}
