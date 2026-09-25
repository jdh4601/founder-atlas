import { extractWikilinkSlugs } from "./markdown";
import type { KeywordPage } from "./types";

/**
 * Returns every keyword page whose body links `[[slug]]` to the given
 * keyword, excluding the page itself.
 */
export function getBacklinksFor(
  pages: readonly KeywordPage[],
  slug: string,
): KeywordPage[] {
  return pages.filter(
    (page) =>
      page.slug !== slug && extractWikilinkSlugs(page.body).includes(slug),
  );
}
