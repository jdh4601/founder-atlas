import type { AskResult } from "./ask";
import { buildEvidenceLink } from "./evidence";
import { getKeywordBySlug } from "./keywords";
import { getAdviceById } from "./advice";
import { getSourceById } from "./sources";
import type { Advice, KeywordPage, Source } from "./types";

export interface MatchedKeywordPage {
  readonly slug: string;
  readonly title: string;
  readonly summary: string;
}

export interface AskEvidence {
  readonly adviceId: string;
  readonly claim: string;
  readonly sourceTitle: string;
  readonly url: string;
  readonly label: string;
}

export interface AskApiResponse {
  readonly answered: boolean;
  readonly answer: string | null;
  readonly matchedPages: readonly MatchedKeywordPage[];
  readonly evidence: readonly AskEvidence[];
}

/**
 * Turns the id-only `AskResult` from `lib/ask.ts` into a response the
 * client can render directly, without needing filesystem access of its
 * own: matched keyword slugs become title+summary, cited advice ids become
 * evidence chips (claim + source title + evidence link).
 */
export function buildAskResponse(
  result: AskResult,
  keywordPages: readonly KeywordPage[],
  advice: readonly Advice[],
  sources: readonly Source[],
): AskApiResponse {
  return {
    answered: result.answered,
    answer: result.answer,
    matchedPages: buildMatchedPages(result.matched, keywordPages),
    evidence: buildEvidence(result.citedAdvice, advice, sources),
  };
}

function buildMatchedPages(
  matchedSlugs: readonly string[],
  keywordPages: readonly KeywordPage[],
): MatchedKeywordPage[] {
  return matchedSlugs.flatMap((slug) => {
    const page = getKeywordBySlug(keywordPages, slug);
    if (!page) return [];
    return [{ slug: page.slug, title: page.title, summary: page.summary }];
  });
}

function buildEvidence(
  citedAdviceIds: readonly string[],
  advice: readonly Advice[],
  sources: readonly Source[],
): AskEvidence[] {
  return citedAdviceIds.flatMap((id) => {
    const unit = getAdviceById(advice, id);
    if (!unit) return [];
    const source = getSourceById(sources, unit.source);
    if (!source) return [];
    const link = buildEvidenceLink(unit, source);
    return [
      {
        adviceId: unit.id,
        claim: unit.claim,
        sourceTitle: source.titleKo,
        url: link.url,
        label: link.label,
      },
    ];
  });
}
