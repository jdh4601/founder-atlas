"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { sortByPublished, type BrowseSource, type PublishedOrder } from "@/lib/sourceBrowse";

interface SourceBrowserProps {
  /** Contents already narrowed by the category and keyword selection. */
  readonly sources: readonly BrowseSource[];
  readonly total: number;
  /** The selected keyword or category title, shown next to the heading. */
  readonly filterLabel: string | null;
}

export function SourceBrowser({ sources, total, filterLabel }: SourceBrowserProps) {
  const [query, setQuery] = useState("");
  const [order, setOrder] = useState<PublishedOrder>("newest");
  const filtered = useMemo(() => {
    const normalizedQuery = query.trim().toLocaleLowerCase();
    const matching = sources.filter(
      (source) =>
        !normalizedQuery ||
        `${source.title} ${source.origin} ${source.speakers.join(" ")}`
          .toLocaleLowerCase()
          .includes(normalizedQuery),
    );
    return sortByPublished(matching, order);
  }, [sources, query, order]);

  return (
    <div>
      <div className="flex flex-col gap-3 border-b border-line pb-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-[18px] font-semibold tracking-tight text-ink">
            원문 콘텐츠{filterLabel && <span className="ml-2 font-normal text-ink-muted">#{filterLabel}</span>}
          </h2>
          <p className="mt-1 text-sm text-ink-muted">수집한 영상과 글 {total}개</p>
        </div>
        <div className="flex w-full gap-2 sm:max-w-[400px]">
          <label className="block min-w-0 flex-1">
            <span className="sr-only">콘텐츠 검색</span>
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="제목이나 출처 검색"
              className="w-full rounded-lg border border-line bg-surface px-3.5 py-2.5 text-sm text-ink placeholder:text-ink-muted focus:border-focus focus:outline-none"
            />
          </label>
          <label className="block shrink-0">
            <span className="sr-only">정렬</span>
            <select
              value={order}
              onChange={(event) => setOrder(event.target.value as PublishedOrder)}
              className="h-full rounded-lg border border-line bg-surface px-3 py-2.5 text-sm text-ink focus:border-focus focus:outline-none"
            >
              <option value="newest">최신순</option>
              <option value="oldest">오래된순</option>
            </select>
          </label>
        </div>
      </div>

      <p className="py-5 text-sm text-ink-muted" aria-live="polite">{filtered.length}개 콘텐츠</p>
      {filtered.length === 0 ? (
        <p className="border-t border-line py-16 text-center text-sm text-ink-muted">일치하는 콘텐츠가 없습니다. 검색어나 키워드를 바꿔보세요.</p>
      ) : (
        <ul aria-label="콘텐츠 목록" className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-3 xl:grid-cols-4">
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
                  <h2 className="line-clamp-3 text-[14px] font-semibold leading-snug text-ink transition-colors group-hover:text-focus sm:text-[15px]">{source.title}</h2>
                  <p className="mt-2 line-clamp-2 text-[11px] text-ink-muted sm:text-xs">
                    {source.origin} · {source.format}{source.published ? ` · ${source.published}` : ""}
                  </p>
                  {source.speakers.length > 0 && <p className="mt-1 line-clamp-1 text-xs text-ink-muted">{source.speakers.join(", ")}</p>}
                  <div className="mt-auto flex flex-wrap gap-1.5 pt-3">
                    {source.tags.slice(0, 3).map((tag) => (
                      <span key={tag.slug} className="rounded-full bg-focus-soft px-2 py-1 text-xs text-ink-muted">#{tag.title}</span>
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
