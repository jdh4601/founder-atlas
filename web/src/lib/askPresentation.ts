import type { AskResult } from "./ask";
import { buildEvidenceEntries, type EvidenceEntry } from "./evidence";
import { getKeywordBySlug } from "./keywords";
import type { Advice, KeywordPage, Source } from "./types";

export interface MatchedKeywordPage {
  readonly slug: string;
  readonly title: string;
  readonly summary: string;
}

export interface AskApiResponse {
  readonly answered: boolean;
  readonly answer: string | null;
  readonly matchedPages: readonly MatchedKeywordPage[];
  readonly evidence: readonly EvidenceEntry[];
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
    evidence: buildEvidenceEntries(result.citedAdvice, advice, sources),
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
