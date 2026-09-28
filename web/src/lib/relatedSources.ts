import { toBrowseSources, type BrowseSource } from "./sourceBrowse";
import type { Advice, Source } from "./types";

/** Rank real source pages by shared advice keywords, then browse tags. */
export function relatedSources(
  current: Source,
  sources: readonly Source[],
  advice: readonly Advice[],
): BrowseSource[] {
  const browse = toBrowseSources(sources);
  const currentBrowse = browse.find((source) => source.id === current.id);
  const currentTags = new Set(currentBrowse?.tags ?? []);
  const keywordsBySource = new Map<string, Set<string>>();
  for (const unit of advice) {
    const keywords = keywordsBySource.get(unit.source) ?? new Set<string>();
    for (const keyword of unit.keywords) keywords.add(keyword);
    keywordsBySource.set(unit.source, keywords);
  }
  const currentKeywords = keywordsBySource.get(current.id) ?? new Set<string>();

  const scored = browse
    .filter((candidate) => candidate.id !== current.id)
    .map((candidate) => {
      const sharedKeywords = [...(keywordsBySource.get(candidate.id) ?? [])]
        .filter((keyword) => currentKeywords.has(keyword)).length;
      const sharedTags = candidate.tags.filter((tag) => currentTags.has(tag)).length;
      return {
        candidate,
        score: sharedKeywords * 10 + sharedTags * 4
          + Number(candidate.origin === currentBrowse?.origin)
          + Number(candidate.format === currentBrowse?.format),
      };
    });
  scored.sort((a, b) =>
    b.score - a.score
    || (b.candidate.published ?? "").localeCompare(a.candidate.published ?? "")
    || a.candidate.id.localeCompare(b.candidate.id),
  );
  return scored.slice(0, 2).map(({ candidate }) => candidate);
}
