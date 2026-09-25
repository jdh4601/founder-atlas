import { notFound } from "next/navigation";
import { getAdviceByIds, matchesProfile, sortAdviceByProfile } from "@/lib/advice";
import { getBacklinksFor } from "@/lib/backlinks";
import { getContentDir } from "@/lib/contentDir";
import { buildEvidenceEntries } from "@/lib/evidence";
import { getKeywordBySlug } from "@/lib/keywords";
import { findCategory, findKeywordTitle } from "@/lib/taxonomy";
import { getSiteData } from "@/lib/site";
import { BacklinksList } from "@/components/BacklinksList";
import { CategoryChip } from "@/components/CategoryChip";
import { EvidenceChip } from "@/components/EvidenceChip";
import { MarkdownBody } from "@/components/MarkdownBody";
import { ReviewBadge } from "@/components/ReviewBadge";
import { SourceThumbnails } from "@/components/SourceThumbnails";

interface KeywordPageProps {
  readonly params: Promise<{ slug: string }>;
}

export default async function KeywordPage({ params }: KeywordPageProps) {
  const { slug } = await params;
  const { taxonomy, profile, keywordPages, advice, sources } = getSiteData(
    getContentDir(),
  );

  const page = getKeywordBySlug(keywordPages, slug);
  if (!page) notFound();

  const category = findCategory(taxonomy, page.category);
  const pageSources = sourcesForAdvice(page.advice, advice, sources);
  const evidenceEntries = buildEvidenceEntries(page.advice, advice, sources);
  const evidenceById = new Map(evidenceEntries.map((e) => [e.adviceId, e]));
  const sortedAdvice = sortAdviceByProfile(
    getAdviceByIds(advice, page.advice),
    profile,
  );
  const backlinks = getBacklinksFor(keywordPages, slug);

  return (
    <div className="mx-auto max-w-[720px] px-5 pb-24 pt-12">
      <div className="flex flex-wrap items-center gap-3">
        {category && <CategoryChip title={category.title} color={category.color} />}
        {!page.reviewed && <ReviewBadge />}
      </div>
      <h1 className="mt-2 text-[26px] font-semibold leading-snug text-ink">
        {page.title}
      </h1>
      <p className="mt-2 text-[14.5px] leading-relaxed text-ink-muted">
        {page.summary}
      </p>

      {pageSources.length > 0 && (
        <div className="mt-6">
          <SourceThumbnails sources={pageSources} />
        </div>
      )}

      <div className="mt-8">
        <MarkdownBody
          markdown={page.body}
          titleFor={(s) => findKeywordTitle(taxonomy, s)}
          evidenceById={evidenceById}
        />
      </div>

      {evidenceEntries.length > 0 && (
        <section className="mt-10 border-t border-line pt-6">
          <h2 className="text-[15px] font-semibold text-ink">근거 모아보기</h2>
          <div className="mt-3 space-y-2.5">
            {sortedAdvice.map((unit) => {
              const evidence = evidenceById.get(unit.id);
              if (!evidence) return null;
              return (
                <EvidenceChip
                  key={unit.id}
                  evidence={evidence}
                  matchesProfile={matchesProfile(unit, profile)}
                />
              );
            })}
          </div>
        </section>
      )}

      <BacklinksList pages={backlinks} />
    </div>
  );
}

function sourcesForAdvice(
  adviceIds: readonly string[],
  advice: ReturnType<typeof getSiteData>["advice"],
  sources: ReturnType<typeof getSiteData>["sources"],
) {
  const sourceIds = new Set(
    adviceIds.flatMap((id) => {
      const unit = advice.find((a) => a.id === id);
      return unit ? [unit.source] : [];
    }),
  );
  return sources.filter((source) => sourceIds.has(source.id));
}
