import Link from "next/link";
import type { KeywordPage } from "@/lib/types";

interface BacklinksListProps {
  readonly pages: readonly KeywordPage[];
}

/** "이 페이지를 언급한 페이지" — other keyword pages that [[link]] here. */
export function BacklinksList({ pages }: BacklinksListProps) {
  if (pages.length === 0) return null;

  return (
    <section className="mt-10 border-t border-line pt-6">
      <h2 className="text-[15px] font-semibold text-ink">이 페이지를 언급한 페이지</h2>
      <ul className="mt-3 flex flex-wrap gap-2">
        {pages.map((page) => (
          <li key={page.slug}>
            <Link
              href={`/k/${page.slug}`}
              className="inline-block rounded-full border border-line px-3 py-1.5 text-[13.5px] text-ink transition-colors hover:border-focus"
            >
              {page.title}
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
