# Founder Atlas

Personal web app: find YC / a16z / Paul Graham advice for a specific startup problem,
organized as keyword pages with exact source timestamps.

- Design decisions: `docs/design.md`
- Data contract (pipeline ↔ web): `docs/content-schema.md` — read before touching either side.

## Directory Structure

```
content/      Markdown data (source of truth). taxonomy.yaml & profile.yaml are hand-edited.
pipeline/     Python (uv): discover → ingest → extract → verify → build-pages
web/          Next.js + TypeScript: /, /k/[slug], /explore, /api/ask
docs/         design.md, content-schema.md
```

## Rules

- Advice `quote` is internal only. Never render it in the UI.
- Timestamps come from code (quote ↔ transcript match), never from the LLM.
- Only advice with `match_score >= 90` is written to `content/advice/`.
- `/api/ask` answers only from advice units; if none match, it logs the question and says so.

## Commands

- Pipeline tests: `cd pipeline && uv run pytest -x -q`
- Web tests: `cd web && npx jest --passWithNoTests`
- Web type check: `cd web && npm run typecheck` (runs `next typegen` first)
- Web build on real data: `cd web && CONTENT_DIR=../content npm run build`
- Pipeline CLI: `cd pipeline && uv run atlas --help` (see pipeline/README.md)
