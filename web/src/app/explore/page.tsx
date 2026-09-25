import { SourceBrowser } from "@/components/SourceBrowser";
import { getContentDir } from "@/lib/contentDir";
import { toBrowseSources } from "@/lib/sourceBrowse";
import { loadSources } from "@/lib/sources";

export default function ExplorePage() {
  const sources = toBrowseSources(loadSources(getContentDir()));
  return (
    <div className="mx-auto max-w-[1100px] px-5 pb-24 pt-9 sm:pt-12">
      <SourceBrowser sources={sources} />
    </div>
  );
}
