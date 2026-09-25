import { z } from "zod";

/**
 * YAML frontmatter dates (e.g. `2026-09-25`, unquoted) are parsed by js-yaml
 * as `Date` objects, not strings. Normalize both shapes to `YYYY-MM-DD`.
 */
export const yamlDateString = z
  .union([z.string(), z.date()])
  .transform((v) => (v instanceof Date ? v.toISOString().slice(0, 10) : v));
