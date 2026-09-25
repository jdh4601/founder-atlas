import type { Source } from "./types";

export interface BrowseSource {
  readonly id: string;
  readonly title: string;
  readonly url: string;
  readonly thumbnail: string | null;
  readonly origin: string;
  readonly format: string;
  readonly published: string | null;
  readonly speakers: readonly string[];
  readonly tags: readonly string[];
}

const originLabels: Record<Source["origin"], string> = {
  "yc-youtube": "YC",
  lightcone: "Lightcone",
  "paul-graham": "PaulGraham",
  a16z: "a16z",
};

const formatLabels: Record<Source["format"], string> = {
  video: "영상",
  essay: "에세이",
  blog: "아티클",
  podcast: "팟캐스트",
};

// Topic tags are assigned only when these words appear in the source title.
// This makes unprocessed sources browseable without pretending their content
// has already been classified by the advice extraction pipeline.
const titleTopics: readonly { tag: string; pattern: RegExp }[] = [
  { tag: "가격", pattern: /\b(pric(?:e|es|ing)|undercharg(?:e|ing)|packaging)\b/i },
  { tag: "고객", pattern: /\b(customer|customers|users?)\b/i },
  { tag: "영업", pattern: /\b(sales|sell|selling)\b/i },
  { tag: "성장", pattern: /\b(growth|distribution|retention)\b/i },
  { tag: "제품", pattern: /\b(product|products|pmf)\b/i },
  { tag: "투자", pattern: /\b(fundrais(?:e|ing)|funding|investors?|venture capital|vc)\b/i },
  { tag: "채용", pattern: /\b(hiring|hire|recruiting)\b/i },
  { tag: "아이디어", pattern: /\b(ideas?|problem validation)\b/i },
  { tag: "AI", pattern: /\bai\b|artificial intelligence|generative/i },
];

export function toBrowseSources(sources: readonly Source[]): BrowseSource[] {
  return sources
    .map((source) => ({
      id: source.id,
      title: source.titleKo,
      url: source.url,
      thumbnail: source.thumbnail,
      origin: originLabels[source.origin],
      format: formatLabels[source.format],
      published: source.published,
      speakers: source.speakers,
      tags: [
        originLabels[source.origin],
        formatLabels[source.format],
        ...titleTopics
          .filter(({ pattern }) => pattern.test(source.title))
          .map(({ tag }) => tag),
      ],
    }))
    .sort((a, b) =>
      (b.published ?? "").localeCompare(a.published ?? "") ||
      a.title.localeCompare(b.title),
    );
}
