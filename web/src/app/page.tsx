import { AskPanel } from "@/components/AskPanel";
import { ContentExplorer } from "@/components/ContentExplorer";
import { getContentDir } from "@/lib/contentDir";
import { getSiteData } from "@/lib/site";
import { browseCategories, toBrowseSources } from "@/lib/sourceBrowse";

export default function Home() {
  const { taxonomy, keywordPages, sources } = getSiteData(getContentDir());
  const browse = toBrowseSources(sources, taxonomy);
  const categories = browseCategories(taxonomy, browse, new Set(keywordPages.map((page) => page.slug)));

  return (
    <div className="mx-auto max-w-[1100px] px-5 pb-24 pt-8 sm:pt-10">
      <h1 className="sr-only">Founder Atlas</h1>
      <div>
        <AskPanel>
          <ContentExplorer categories={categories} sources={browse} />
        </AskPanel>
      </div>
    </div>
  );
}
