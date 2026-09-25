import { findCategoryForKeyword, findKeywordTitle } from "./taxonomy";
import type { Advice, Graph, GraphEdge, GraphNode, Taxonomy } from "./types";

/**
 * Builds the full-map graph (see `docs/content-schema.md` -> Graph).
 * Nodes are keywords with >=1 advice unit; edge weight between two keywords
 * is the number of advice units tagged with both, plus the number of
 * sources that have advice in both.
 */
export function buildGraph(
  taxonomy: Taxonomy,
  advice: readonly Advice[],
): Graph {
  return {
    nodes: buildNodes(taxonomy, advice),
    edges: buildEdges(advice),
  };
}

function buildNodes(
  taxonomy: Taxonomy,
  advice: readonly Advice[],
): GraphNode[] {
  const adviceCountByKeyword = new Map<string, number>();
  for (const unit of advice) {
    for (const keyword of unit.keywords) {
      adviceCountByKeyword.set(
        keyword,
        (adviceCountByKeyword.get(keyword) ?? 0) + 1,
      );
    }
  }

  const nodes: GraphNode[] = [];
  for (const [slug, adviceCount] of adviceCountByKeyword) {
    const category = findCategoryForKeyword(taxonomy, slug);
    if (!category) continue;
    nodes.push({
      slug,
      title: findKeywordTitle(taxonomy, slug) ?? slug,
      category: category.slug,
      color: category.color,
      adviceCount,
    });
  }
  return nodes;
}

function buildEdges(advice: readonly Advice[]): GraphEdge[] {
  const weightByPair = new Map<string, number>();
  const addWeight = (pair: readonly [string, string]): void => {
    const key = pairKey(pair);
    weightByPair.set(key, (weightByPair.get(key) ?? 0) + 1);
  };

  for (const unit of advice) {
    for (const pair of uniquePairs(unit.keywords)) addWeight(pair);
  }
  for (const keywordSet of keywordSetsBySource(advice).values()) {
    for (const pair of uniquePairs([...keywordSet])) addWeight(pair);
  }

  return [...weightByPair.entries()].map(([key, weight]) => {
    const [source, target] = key.split("::");
    return { source, target, weight };
  });
}

function keywordSetsBySource(
  advice: readonly Advice[],
): Map<string, Set<string>> {
  const keywordsBySource = new Map<string, Set<string>>();
  for (const unit of advice) {
    const set = keywordsBySource.get(unit.source) ?? new Set<string>();
    for (const keyword of unit.keywords) set.add(keyword);
    keywordsBySource.set(unit.source, set);
  }
  return keywordsBySource;
}

function pairKey(pair: readonly [string, string]): string {
  return [...pair].sort().join("::");
}

function uniquePairs(items: readonly string[]): Array<[string, string]> {
  const unique = [...new Set(items)];
  const pairs: Array<[string, string]> = [];
  for (let i = 0; i < unique.length; i++) {
    for (let j = i + 1; j < unique.length; j++) {
      pairs.push([unique[i], unique[j]]);
    }
  }
  return pairs;
}
