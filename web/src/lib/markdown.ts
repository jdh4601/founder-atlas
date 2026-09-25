/**
 * Pure text transforms for keyword page bodies. Kept dependency-free (no
 * remark/unified) so they are trivially unit-testable and so `advice://`
 * links stay valid CommonMark that any markdown renderer parses as a plain
 * link node — `MarkdownBody` then swaps that link for an `EvidenceChip`.
 */

const WIKILINK_PATTERN = /\[\[([a-z0-9-]+)\]\]/g;
const ADVICE_MARKER_PATTERN = /\{\{advice:([a-zA-Z0-9._-]+)\}\}/g;
const CODE_FENCE_PATTERN = /```[\s\S]*?```/g;

export type TitleLookup = (slug: string) => string | undefined;

/** Replaces `[[slug]]` with a markdown link to `/k/slug`. */
export function resolveWikilinks(
  markdown: string,
  titleFor: TitleLookup,
): string {
  return markdown.replace(WIKILINK_PATTERN, (_match, slug: string) => {
    const title = titleFor(slug) ?? slug;
    return `[${title}](/k/${slug})`;
  });
}

/**
 * Replaces `{{advice:id}}` with a markdown link using a custom `advice://`
 * scheme. The visible label is never shown as-is — the `a` renderer in
 * `MarkdownBody` recognizes the scheme and renders an `EvidenceChip`
 * instead, so the label only matters as a no-JS/plaintext fallback.
 */
export function resolveAdviceMarkers(markdown: string): string {
  return markdown.replace(ADVICE_MARKER_PATTERN, (_match, id: string) => {
    return `[근거 보기](advice://${id})`;
  });
}

/** Returns the unique set of keyword slugs referenced via `[[slug]]`. */
export function extractWikilinkSlugs(markdown: string): string[] {
  const slugs = new Set<string>();
  for (const match of markdown.matchAll(WIKILINK_PATTERN)) {
    slugs.add(match[1]);
  }
  return [...slugs];
}

/** Extracts the advice id from an `advice://id` href, or null if not one. */
export function parseAdviceHref(href: string): string | null {
  const match = /^advice:\/\/(.+)$/.exec(href);
  return match ? match[1] : null;
}

/**
 * Applies both transforms while leaving fenced code blocks (including
 * ```mermaid) untouched.
 */
export function transformKeywordMarkdown(
  markdown: string,
  titleFor: TitleLookup,
): string {
  const parts = markdown.split(CODE_FENCE_PATTERN);
  const fences = markdown.match(CODE_FENCE_PATTERN) ?? [];
  const transformedParts = parts.map((part) =>
    resolveAdviceMarkers(resolveWikilinks(part, titleFor)),
  );
  return transformedParts.reduce((acc, part, i) => {
    const fence = fences[i];
    return acc + part + (fence ?? "");
  }, "");
}
