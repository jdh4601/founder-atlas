"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import type { BrowseSource } from "@/lib/sourceBrowse";

interface SourceBrowserProps {
  readonly sources: readonly BrowseSource[];
}

export function SourceBrowser({ sources }: SourceBrowserProps) {
  const [tag, setTag] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const tags = useMemo(() => {
    const counts = new Map<string, number>();
    sources.forEach((source) =>
      source.tags.forEach((value) => counts.set(value, (counts.get(value) ?? 0) + 1)),
    );
    return [...counts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  }, [sources]);
  const filtered = useMemo(() => {
    const normalizedQuery = query.trim().toLocaleLowerCase();
    return sources.filter(
      (source) =>
        (!tag || source.tags.includes(tag)) &&
        (!normalizedQuery ||
          `${source.title} ${source.origin} ${source.speakers.join(" ")}`
            .toLocaleLowerCase()
            .includes(normalizedQuery)),
    );
  }, [sources, tag, query]);

  return (
    <div>
      <div className="flex flex-col gap-4 border-b border-line pb-5 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-ink-muted">Explore</p>
          <h1 className="mt-2 text-[30px] font-semibold tracking-tight text-ink sm:text-[36px]">콘텐츠 탐색</h1>
          <p className="mt-1 text-sm text-ink-muted">수집한 영상과 글 {sources.length}개</p>
        </div>
        <label className="block w-full sm:max-w-[290px]">
          <span className="sr-only">콘텐츠 검색</span>
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="제목이나 출처 검색"
            className="w-full rounded-lg border border-line bg-surface px-3.5 py-2.5 text-sm text-ink placeholder:text-ink-muted focus:border-focus focus:outline-none"
          />
        </label>
      </div>

      <div className="-mx-5 overflow-x-auto border-b border-line px-5 py-4 sm:mx-0 sm:px-0" aria-label="해시태그 필터">
        <div className="flex w-max gap-2">
          <button
            type="button"
            aria-pressed={tag === null}
            onClick={() => setTag(null)}
            className={`rounded-full px-3.5 py-2 text-sm transition-colors ${tag === null ? "bg-ink text-paper" : "bg-surface text-ink hover:bg-focus-soft"}`}
          >
            전체
          </button>
          {tags.map(([value, count]) => (
            <button
              key={value}
              type="button"
              aria-pressed={tag === value}
              onClick={() => setTag(value === tag ? null : value)}
              className={`rounded-full px-3.5 py-2 text-sm transition-colors ${tag === value ? "bg-ink text-paper" : "bg-surface text-ink hover:bg-focus-soft"}`}
            >
              #{value} <span className="ml-1 opacity-60">{count}</span>
            </button>
          ))}
        </div>
      </div>

      <p className="py-5 text-sm text-ink-muted" aria-live="polite">{filtered.length}개 콘텐츠</p>
      {filtered.length === 0 ? (
        <p className="border-t border-line py-16 text-center text-sm text-ink-muted">일치하는 콘텐츠가 없습니다. 검색어나 해시태그를 바꿔보세요.</p>
      ) : (
        <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {filtered.map((source) => (
            <li key={source.id} className="min-w-0">
              <Link
                href={`/source/${source.id}`}
                className="group flex h-full flex-col overflow-hidden rounded-xl border border-line bg-surface transition-colors hover:border-focus/40 hover:shadow-sm"
              >
                <div className="relative aspect-video w-full shrink-0 overflow-hidden bg-focus-soft">
                  {source.thumbnail ? (
                    // Source hosts are varied; remote images are intentionally not optimized.
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={source.thumbnail} alt="" loading="lazy" className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-[1.03]" />
                  ) : (
                    <div className="flex h-full items-center justify-center px-4 text-center text-lg font-semibold text-ink-muted">{source.origin}</div>
                  )}
                  {source.format === "영상" && (
                    <span className="absolute bottom-2 right-2 rounded bg-black/75 px-1.5 py-0.5 text-xs font-medium text-white">영상</span>
                  )}
                </div>
                <div className="flex min-w-0 flex-1 flex-col p-3.5">
                  <h2 className="line-clamp-2 text-[15px] font-semibold leading-snug text-ink transition-colors group-hover:text-focus">{source.title}</h2>
                  <p className="mt-2 text-xs text-ink-muted">
                    {source.origin} · {source.format}{source.published ? ` · ${source.published}` : ""}
                  </p>
                  {source.speakers.length > 0 && <p className="mt-1 line-clamp-1 text-xs text-ink-muted">{source.speakers.join(", ")}</p>}
                  <div className="mt-auto flex flex-wrap gap-1.5 pt-3">
                    {source.tags.map((value) => (
                      <span key={value} className="rounded-full bg-focus-soft px-2 py-1 text-xs text-ink-muted">#{value}</span>
                    ))}
                  </div>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
