/**
 * Types mirroring `docs/content-schema.md`. This file is the TypeScript side
 * of the contract with `pipeline/`. Keep field names identical to the
 * frontmatter keys so `gray-matter` output can be narrowed directly.
 */

export const STAGES = [
  "idea",
  "pre-seed",
  "seed",
  "series-a",
  "growth",
] as const;
export type Stage = (typeof STAGES)[number];

export const DOMAINS = [
  "ai",
  "b2b",
  "b2c",
  "saas",
  "marketplace",
  "devtools",
  "consumer",
  "hardware",
] as const;
export type Domain = (typeof DOMAINS)[number];

export const ORIGINS = [
  "yc-youtube",
  "lightcone",
  "paul-graham",
  "a16z",
] as const;
export type Origin = (typeof ORIGINS)[number];

export const SOURCE_FORMATS = ["video", "essay", "blog", "podcast"] as const;
export type SourceFormat = (typeof SOURCE_FORMATS)[number];

export interface TaxonomyKeyword {
  readonly slug: string;
  readonly title: string;
}

export interface TaxonomyCategory {
  readonly slug: string;
  readonly title: string;
  readonly color: string;
  readonly keywords: readonly TaxonomyKeyword[];
}

export interface Taxonomy {
  readonly categories: readonly TaxonomyCategory[];
}

export interface Profile {
  readonly stage: Stage;
  readonly domain: readonly Domain[];
}

export interface Source {
  readonly id: string;
  readonly title: string;
  readonly titleKo: string;
  readonly url: string;
  readonly origin: Origin;
  readonly format: SourceFormat;
  readonly youtubeId: string | null;
  readonly published: string | null;
  readonly speakers: readonly string[];
  readonly thumbnail: string | null;
  readonly images: readonly string[];
  readonly ingestedAt: string;
  readonly summary: string;
}

export interface AdviceContext {
  readonly stage: readonly Stage[];
  readonly domain: readonly Domain[];
}

export type AdviceAnchor =
  | { readonly kind: "timestamp"; readonly start: number }
  | { readonly kind: "paragraph"; readonly paragraph: number };

/**
 * The advice unit as used by the web app. Note there is no `quote` field:
 * it is stripped in `lib/advice.ts` and must never reach a client component.
 */
export interface Advice {
  readonly id: string;
  readonly source: string;
  readonly category: string;
  readonly keywords: readonly string[];
  readonly context: AdviceContext;
  readonly speaker: string | null;
  readonly claim: string;
  readonly anchor: AdviceAnchor;
  readonly matchScore: number;
  readonly body: string;
}

export interface KeywordImage {
  readonly src: string;
  readonly alt: string;
  readonly source: string;
}

export interface KeywordPage {
  readonly slug: string;
  readonly title: string;
  readonly category: string;
  readonly summary: string;
  readonly reviewed: boolean;
  readonly advice: readonly string[];
  readonly images: readonly KeywordImage[];
  readonly updatedAt: string;
  readonly body: string;
}

export interface QuestionLogEntry {
  readonly ts: string;
  readonly question: string;
  readonly matched: readonly string[];
  readonly answered: boolean;
  readonly answer: string | null;
  readonly citedAdvice: readonly string[];
  readonly clicked: string | null;
}

export interface GraphNode {
  readonly slug: string;
  readonly title: string;
  readonly category: string;
  readonly color: string;
  readonly adviceCount: number;
}

export interface GraphEdge {
  readonly source: string;
  readonly target: string;
  readonly weight: number;
}

export interface Graph {
  readonly nodes: readonly GraphNode[];
  readonly edges: readonly GraphEdge[];
}
