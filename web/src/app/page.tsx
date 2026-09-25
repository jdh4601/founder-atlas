import { AskPanel } from "@/components/AskPanel";
import { CategoryExplorer } from "@/components/CategoryExplorer";
import { getContentDir } from "@/lib/contentDir";
import { getSiteData } from "@/lib/site";

export default function Home() {
  const { taxonomy, keywordPages } = getSiteData(getContentDir());

  return (
    <div className="mx-auto max-w-[1100px] px-5 pb-24 pt-14 sm:pt-20">
      <div className="mx-auto max-w-[640px]">
        <h1 className="text-[26px] font-semibold leading-snug text-ink sm:text-[30px]">
          지금 어떤 문제에 부딪혔나요?
        </h1>
        <p className="mt-2 text-[14.5px] text-ink-muted">
          YC, a16z, Paul Graham이 이 문제에 대해 어떻게 말했는지 찾아드려요.
        </p>
        <div className="mt-6">
          <AskPanel />
        </div>
      </div>

      <div className="mt-20">
        <CategoryExplorer taxonomy={taxonomy} keywordPages={keywordPages} />
      </div>
    </div>
  );
}
