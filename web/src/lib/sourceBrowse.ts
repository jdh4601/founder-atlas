import type { Source, Taxonomy } from "./types";

export interface BrowseTag {
  readonly slug: string;
  readonly title: string;
}

export interface BrowseSource {
  readonly id: string;
  readonly title: string;
  readonly url: string;
  readonly thumbnail: string | null;
  readonly origin: string;
  readonly format: string;
  readonly published: string | null;
  readonly speakers: readonly string[];
  /** Taxonomy keywords the article covers, most central first. */
  readonly tags: readonly BrowseTag[];
}

export interface BrowseKeyword extends BrowseTag {
  readonly count: number;
  readonly hasPage: boolean;
}

export interface BrowseCategory {
  readonly slug: string;
  readonly title: string;
  readonly color: string;
  /** Contents tagged with at least one keyword of this category. */
  readonly count: number;
  readonly keywords: readonly BrowseKeyword[];
}

export type PublishedOrder = "newest" | "oldest";

const originLabels: Record<Source["origin"], string> = {
  "yc-youtube": "YC",
  lightcone: "Lightcone",
  "paul-graham": "PaulGraham",
  a16z: "a16z",
  insights: "인사이트",
};

const formatLabels: Record<Source["format"], string> = {
  video: "영상",
  essay: "에세이",
  blog: "아티클",
  podcast: "팟캐스트",
};

function keywordTitles(taxonomy: Taxonomy): Map<string, string> {
  return new Map(
    taxonomy.categories.flatMap((category) =>
      category.keywords.map((keyword) => [keyword.slug, keyword.title] as const),
    ),
  );
}

/** Tags are the article's keyword slugs; slugs missing from the taxonomy are dropped. */
export function toBrowseSources(sources: readonly Source[], taxonomy: Taxonomy): BrowseSource[] {
  const titles = keywordTitles(taxonomy);
  const browse = sources.map((source) => ({
    id: source.id,
    title: source.titleKo,
    url: source.url,
    thumbnail: source.thumbnail,
    origin: originLabels[source.origin],
    format: formatLabels[source.format],
    published: source.published,
    speakers: source.speakers,
    tags: (source.tags ?? []).flatMap((slug) => {
      const title = titles.get(slug);
      return title ? [{ slug, title }] : [];
    }),
  }));
  return sortByPublished(browse, "newest");
}

/** Sorts by publish date; undated sources always come last, then by title. */
export function sortByPublished(sources: readonly BrowseSource[], order: PublishedOrder): BrowseSource[] {
  const direction = order === "newest" ? -1 : 1;
  return [...sources].sort((a, b) => {
    if (a.published && b.published && a.published !== b.published) {
      return direction * a.published.localeCompare(b.published);
    }
    if (Boolean(a.published) !== Boolean(b.published)) return a.published ? -1 : 1;
    return a.title.localeCompare(b.title);
  });
}

/** Taxonomy with per-keyword content counts; keywords and categories with no contents are hidden. */
export function browseCategories(
  taxonomy: Taxonomy,
  sources: readonly BrowseSource[],
  pageSlugs: ReadonlySet<string>,
): BrowseCategory[] {
  const counts = new Map<string, number>();
  for (const source of sources) {
    for (const tag of source.tags) counts.set(tag.slug, (counts.get(tag.slug) ?? 0) + 1);
  }
  return taxonomy.categories.flatMap((category) => {
    const slugs = new Set(category.keywords.map((keyword) => keyword.slug));
    const keywords = category.keywords
      .map((keyword) => ({
        slug: keyword.slug,
        title: keyword.title,
        count: counts.get(keyword.slug) ?? 0,
        hasPage: pageSlugs.has(keyword.slug),
      }))
      .filter((keyword) => keyword.count > 0);
    if (keywords.length === 0) return [];
    const count = sources.filter((source) => source.tags.some((tag) => slugs.has(tag.slug))).length;
    return [{ slug: category.slug, title: category.title, color: category.color, count, keywords }];
  });
}
