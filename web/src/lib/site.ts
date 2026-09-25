import { loadAdvice } from "./advice";
import { buildGraph } from "./graph";
import { loadKeywordPages } from "./keywords";
import { loadProfile } from "./profile";
import { loadSources } from "./sources";
import { loadTaxonomy } from "./taxonomy";
import type { Advice, Graph, KeywordPage, Profile, Source, Taxonomy } from "./types";

export interface SiteData {
  readonly taxonomy: Taxonomy;
  readonly profile: Profile;
  readonly keywordPages: readonly KeywordPage[];
  readonly advice: readonly Advice[];
  readonly sources: readonly Source[];
  readonly graph: Graph;
}

/**
 * Loads every `content/` collection pages need, in one place, so server
 * components don't each re-implement the same set of loader calls.
 */
export function getSiteData(contentDir: string): SiteData {
  const taxonomy = loadTaxonomy(contentDir);
  const advice = loadAdvice(contentDir);
  return {
    taxonomy,
    profile: loadProfile(contentDir),
    keywordPages: loadKeywordPages(contentDir),
    advice,
    sources: loadSources(contentDir),
    graph: buildGraph(taxonomy, advice),
  };
}
