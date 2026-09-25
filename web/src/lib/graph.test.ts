import path from "node:path";
import { loadAdvice } from "./advice";
import { buildGraph } from "./graph";
import { loadTaxonomy } from "./taxonomy";
import type { Graph } from "./types";

const FIXTURES_DIR = path.join(__dirname, "../../__fixtures__/content");

function findEdgeWeight(
  graph: Graph,
  a: string,
  b: string,
): number | undefined {
  return graph.edges.find(
    (edge) =>
      (edge.source === a && edge.target === b) ||
      (edge.source === b && edge.target === a),
  )?.weight;
}

describe("buildGraph", () => {
  const taxonomy = loadTaxonomy(FIXTURES_DIR);
  const advice = loadAdvice(FIXTURES_DIR);
  const graph = buildGraph(taxonomy, advice);

  it("creates one node per keyword with >=1 advice, sized by advice count", () => {
    expect(graph.nodes).toHaveLength(3);
    const bySlug = new Map(graph.nodes.map((n) => [n.slug, n]));
    expect(bySlug.get("first-customers")?.adviceCount).toBe(3);
    expect(bySlug.get("pricing-strategy")?.adviceCount).toBe(4);
    expect(bySlug.get("unit-economics")?.adviceCount).toBe(3);
  });

  it("colors each node by its taxonomy category", () => {
    const bySlug = new Map(graph.nodes.map((n) => [n.slug, n]));
    expect(bySlug.get("first-customers")).toMatchObject({
      category: "sales",
      color: "#81B29A",
    });
    expect(bySlug.get("pricing-strategy")).toMatchObject({
      category: "pricing",
      color: "#9B5DE5",
    });
  });

  it("weighs an edge by advice units tagged with both keywords plus sources with advice in both", () => {
    // advice units tagged with both: 1 (lightcone--02)
    // sources with advice in both: lightcone-sample-enterprise-first-customers, paul-graham-sample-do-things-that-dont-scale
    expect(findEdgeWeight(graph, "first-customers", "pricing-strategy")).toBe(
      3,
    );
    // advice units tagged with both: 1 (yc-youtube--02)
    // sources with advice in both: lightcone-sample-enterprise-first-customers, yc-youtube-sample-pricing-lesson
    expect(findEdgeWeight(graph, "pricing-strategy", "unit-economics")).toBe(
      3,
    );
    // no advice unit tags both directly; only lightcone's source ties them
    expect(findEdgeWeight(graph, "first-customers", "unit-economics")).toBe(
      1,
    );
  });

  it("has no self-edges and no duplicate edges for the same pair", () => {
    for (const edge of graph.edges) {
      expect(edge.source).not.toBe(edge.target);
    }
    const seen = new Set<string>();
    for (const edge of graph.edges) {
      const key = [edge.source, edge.target].sort().join("::");
      expect(seen.has(key)).toBe(false);
      seen.add(key);
    }
  });
});
