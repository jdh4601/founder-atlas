# Founder Atlas — web

Next.js (App Router) + TypeScript front end for Founder Atlas. Reads
Markdown/YAML from `content/` (written by `pipeline/`) and serves three
pages plus one API route. See the repo-root `CLAUDE.md` and
`docs/content-schema.md` for the full data contract — this file only
covers `web/`.

## Routes

| Route | What it does |
|---|---|
| `/` | Input-first home: a large "지금 어떤 문제에 부딪혔나요?" question box, plus the 8 taxonomy categories showing only the keywords that already have a page. Asking calls `/api/ask` and renders a short answer, matched keyword pages, and evidence chips (or a "아직 정리되지 않은 주제예요" message when nothing matched). |
| `/k/[slug]` | One keyword page: category chip, an "AI 정리 · 검수 전" badge while `reviewed: false`, source thumbnails, the Markdown body (wikilinks, inline evidence chips, client-rendered Mermaid diagrams), a profile-sorted "근거 모아보기" evidence list, and "이 페이지를 언급한 페이지" backlinks. |
| `/explore` | A list of collected source videos and articles with thumbnail, source, date, title search, and hashtag filters. Hashtags come from source origin, format, and literal terms in the source title. |
| `/map` | Redirects existing links to `/explore`. |
| `POST /api/ask` | Two-step answer flow: (1) match the question to 0–3 real keyword slugs, (2) if matched, draft a 2–3 sentence Korean answer grounded only in those keywords' advice (never the hidden `quote` field), citing advice ids. The request can select Anthropic API, Codex CLI, or Claude Code CLI. Every successfully processed question is appended to `content/questions/log.jsonl`. |

## Setup

```bash
npm install
npm run dev
```

For Anthropic API mode or the pipeline commands, create a repo-root `.env`
from `.env.example` and replace its placeholder with a real API key.

To run against the checked-in sample content while the pipeline is incomplete,
set `CONTENT_DIR=./__fixtures__/content` when starting the server. The default
is the real `../content/` directory.

`ANTHROPIC_API_KEY` is read from the environment, or from a repo-root
`.env` (one level above `web/`) if unset — Next.js only auto-loads
`web/.env*`, so `lib/env.ts` loads the repo-root file explicitly. A
missing key makes Anthropic API requests return a clear `500`, it never silently
no-ops. The question form can instead select Codex CLI or Claude Code CLI.
Those options execute the installed CLI on the **web server** using its existing
login, so they are intended for a local server; installing a CLI only on the
browser user's machine is insufficient. They do not need `ANTHROPIC_API_KEY`.
If a selected CLI is unavailable or fails, `/api/ask` returns `503`.

## Directory structure

```
src/
├── app/
│   ├── page.tsx            /  (AskPanel + CategoryExplorer)
│   ├── k/[slug]/page.tsx   /k/[slug]
│   ├── explore/page.tsx    /explore (source browser)
│   ├── map/page.tsx        /map → /explore
│   └── api/ask/route.ts    POST /api/ask
├── components/              One component per file, PascalCase.
│   ├── AskPanel.tsx          Client: question input + fetch + results
│   ├── AskResults.tsx        Answer + matched pages + evidence
│   ├── MarkdownBody.tsx      react-markdown + custom renderers
│   ├── MermaidDiagram.tsx    Client: mermaid.render() for ```mermaid
│   ├── SourceBrowser.tsx     Client: title search + hashtag filters + source list
│   ├── EvidenceChip.tsx / InlineEvidenceLink.tsx
│   ├── CategoryChip.tsx / CategoryExplorer.tsx
│   ├── ReviewBadge.tsx / SourceThumbnails.tsx / BacklinksList.tsx
└── lib/                      Data layer — pure functions, no React.
    ├── contentDir.ts         Resolves CONTENT_DIR
    ├── yaml.ts, types.ts     Shared types + YAML date coercion
    ├── taxonomy.ts / profile.ts / sources.ts / advice.ts / keywords.ts
    │                         Load + validate (zod) each content/ collection
    ├── markdown.ts           [[wikilink]] / {{advice:id}} transforms
    ├── backlinks.ts          Pages that [[link]] to a given slug
    ├── sourceBrowse.ts        Source metadata → browse items and title-backed tags
    ├── evidence.ts            Evidence link/label building (timestamp/paragraph)
    ├── site.ts                Loads every collection in one call
    ├── env.ts                 Repo-root .env loader
    ├── questionsLog.ts        Appends content/questions/log.jsonl
    ├── anthropicClient.ts     Injectable AnthropicJsonClient (real SDK adapter)
    ├── cliClients.ts           Local Codex CLI and Claude Code CLI adapters
    ├── ask.ts                 /api/ask's two-step matching + answering logic
    └── askPresentation.ts     Turns AskResult (ids) into the API's JSON shape
```

`lib/*` has no React or Next.js imports — it's plain, unit-tested
TypeScript, loaded by both server components and the API route.

## Content fixtures

`__fixtures__/content/` is a small, clearly-labeled sample dataset (every
title/body is prefixed `[샘플 데이터]`) used by tests and local dev. It
mirrors the real schema exactly — see `docs/content-schema.md`.

## Commands

```bash
npx jest --passWithNoTests   # unit tests (lib/, api/ask/route.test.ts)
npm run typecheck            # route type generation + TypeScript check
npm run build                # production build (must succeed before ship)
npm run lint                 # eslint
```

## Notable implementation notes

- `lib/ask.ts` never sees the Anthropic SDK directly — it depends on the
  small `AnthropicJsonClient` interface from `lib/anthropicClient.ts`, so
  tests inject a mock instead of hitting the network.
- The advice `quote` field is stripped by `lib/advice.ts`'s zod schema
  (schemas omit it, so zod's default "strip unknown keys" behavior drops
  it) before it ever reaches an `Advice` object — see the test in
  `lib/advice.test.ts` that asserts no `SAMPLE QUOTE` text appears
  anywhere in a loaded unit.
- `js-yaml` v5's ESM build (`js-yaml/dist/js-yaml.mjs`) has no default
  export, so `taxonomy.ts`/`profile.ts` use `import * as YAML from
  "js-yaml"` — a plain default import type-checks (via
  `esModuleInterop`) but fails at runtime under Turbopack.
