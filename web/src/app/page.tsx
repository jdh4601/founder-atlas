import { AskPanel } from "@/components/AskPanel";
import { CategoryExplorer } from "@/components/CategoryExplorer";
import { SourceBrowser } from "@/components/SourceBrowser";
import { getContentDir } from "@/lib/contentDir";
import { getSiteData } from "@/lib/site";
import { toBrowseSources } from "@/lib/sourceBrowse";
import { categoriesWithPages } from "@/lib/taxonomy";

export default function Home() {
  const { taxonomy, keywordPages, sources } = getSiteData(getContentDir());
  const groups = categoriesWithPages(taxonomy, keywordPages);

  return (
    <div className="mx-auto max-w-[1100px] px-5 pb-24 pt-12 sm:pt-16">
      <h1 className="text-[26px] font-semibold leading-snug text-ink sm:text-[30px]">
        지금 어떤 문제에 부딪혔나요?
      </h1>
      <p className="mt-2 text-[14.5px] text-ink-muted">
        YC, a16z, Paul Graham이 이 문제에 대해 어떻게 말했는지 찾아드려요.
      </p>
      <div className="mt-6">
        <AskPanel>
          <section id="keywords" className="mt-12 scroll-mt-20">
            <h2 className="text-[18px] font-semibold tracking-tight text-ink">범주별 키워드</h2>
            <div className="mt-3">
              <CategoryExplorer groups={groups} />
            </div>
          </section>
          <section id="contents" className="mt-14 scroll-mt-20">
            <SourceBrowser sources={toBrowseSources(sources)} />
          </section>
        </AskPanel>
      </div>
    </div>
  );
}
