# Content Schema (contract between `pipeline/` and `web/`)

All data lives under `content/`. The pipeline writes it; the web app only reads it
(except `content/questions/log.jsonl`, which the web app appends to).
Markdown files use YAML frontmatter. Slugs are lowercase kebab-case ASCII.

```
content/
├── taxonomy.yaml          # 8 categories + keywords (hand-edited)
├── profile.yaml           # "my situation" (hand-edited)
├── sources/
│   ├── {source_id}.md             # metadata + Korean one-paragraph summary
│   └── {source_id}.transcript.json   # internal raw text, never shown in UI
├── source_articles/{source_id}.md     # Korean reading article generated from raw source
├── advice/{advice_id}.md  # one advice unit
├── keywords/{slug}.md     # one keyword page (human-reviewed)
└── questions/log.jsonl    # one JSON object per question
```

## taxonomy.yaml

```yaml
categories:
  - slug: idea            # one of 8 fixed slugs
    title: 아이디어·문제 발견
    color: "#..."         # category accent color in the web UI
    keywords:
      - slug: problem-validation
        title: 문제 검증
```

Rules: exactly 8 categories; max 20 keywords per category; keyword slugs are globally unique.

## profile.yaml

```yaml
stage: pre-seed           # idea | pre-seed | seed | series-a | growth
domain: [ai, b2b]         # any of: ai, b2b, b2c, saas, marketplace, devtools, consumer, hardware
```

## sources/{source_id}.md

`source_id` = `{origin}-{slug}` e.g. `yc-youtube-how-to-price-your-product`.

```yaml
---
id: yc-youtube-how-to-price-your-product
title: How to Price Your Product         # original title
title_ko: 제품 가격을 정하는 법            # Korean title; '' until written (ingest needs no API key), UI falls back to title
url: https://www.youtube.com/watch?v=XXXXXXXXXXX   # '' for insight memos with no public original
origin: yc-youtube        # yc-youtube | lightcone | paul-graham | a16z | elad-gil | reid-hoffman | andrew-chen | justin-kan | sarah-guo | li-jin | amjad-masad | alexandr-wang | insights
format: video             # video | essay | blog | podcast
youtube_id: XXXXXXXXXXX   # only when format is video/podcast on YouTube
published: 2024-03-01     # may be null
speakers: [Kevin Hale]
thumbnail: https://i.ytimg.com/vi/XXXXXXXXXXX/hqdefault.jpg   # may be null
images: []                # extra image URLs (og:image, in-article images)
ingested_at: 2026-09-25
---
한국어 요약 한 문단.
```

## sources/{source_id}.transcript.json

```json
{
  "kind": "segments",          // "segments" for video, "paragraphs" for text
  "segments": [{ "start": 12.4, "duration": 3.1, "text": "..." }],
  "paragraphs": ["...", "..."]
}
```

Only one of `segments` / `paragraphs` is present.

## Founder and investor blogs

Blog origins are decided by host (e.g. `blog.eladgil.com` -> `elad-gil`).
Reid Hoffman's writing lives on LinkedIn and Greylock, so it is ingested with
`atlas ingest --from-file ... --origin reid-hoffman`. `speakers` is the author.
Relative image URLs and LinkedIn's logo are not used as covers. Posts whose only
cover is a repeated site image have `thumbnail: null` until an AI thumbnail is
made (`docs/notes/pending-thumbnail-concepts.json`).

## Insight notes (`origin: insights`)

`atlas import-insights <vault>` imports `07_Insights/*.md` from the Obsidian vault
as `insights-{NNN}` sources. The article body is the note's numbered insight
sections; personal sections (why it matters to me, linked notes, to-dos, the
original backlink) are dropped and wikilinks become plain text. A model writes
only `title_ko` (a founder-facing claim, not "X interview"), `tldr`, and `lead`;
`tags` are then set by `tag-articles` (below). YouTube notes use the video thumbnail and Korean/English captions as the
transcript; others keep the note paragraphs as the transcript.
Notes listed in `content/insights-exclude.txt` (one source id per line, `#` comments)
are skipped, so deleted off-topic notes are not imported again.

## source_articles/{source_id}.md

`atlas write-source-articles --all --jobs 4` generates one source-grounded
Korean article per ingested transcript. It resumes unchanged files using the
SHA-256 of the raw transcript.

```yaml
---
source: yc-youtube-how-to-price-your-product
title_ko: 제품 가격을 정하는 법
tldr: 가격은 고객이 이해하는 가치 단위에 맞춰 정한다.
lead: 한국어 도입 문단
source_sha256: 64-character hexadecimal digest
generated_at: 2026-09-27
---
## 첫 번째 소제목

원문을 한국어로 재구성한 본문.
```

Figures are placed in the body as `![alt](<url> "caption")` after a paragraph;
the web renders each as a captioned figure and every caption ends with its
source. `atlas add-figures` writes them (2-5 per article; all original images
for blog posts). Video frames and downloaded search images live in
`web/public/figures/{source_id}/` and are referenced as `/figures/...`.
Video frame timestamps come from code (transcript quote match), never the model.
`write-source-articles --force` rewrites the body, so run `add-figures` again after it.

The web detail page displays a one-sentence summary, this article, and two
related source links when present, and uses collected
source `thumbnail`/`images` for its gallery. It otherwise displays the
existing advice-based view.

## advice/{advice_id}.md

`advice_id` = `{source_id}--{nn}` (two-digit index).

```yaml
---
id: yc-youtube-how-to-price-your-product--03
source: yc-youtube-how-to-price-your-product
category: pricing                   # category slug
keywords: [pricing, first-customers]  # 1-3 keyword slugs from taxonomy.yaml
context:
  stage: [pre-seed, seed]           # empty list = applies to all
  domain: [b2b]
speaker: Kevin Hale                 # may be null
claim: 초기 B2B 제품은 가격을 높게 시작하라   # one-line Korean claim (title)
quote: "Charge more than you think..."       # HIDDEN. Verbatim English. Never render.
anchor:
  kind: timestamp                   # timestamp | paragraph
  start: 750                        # seconds (int), computed by code from the quote match
  paragraph: null                   # 0-based paragraph index when kind is paragraph
match_score: 96.5                   # rapidfuzz score, must be >= 90
---
한국어 본문: 조언 설명 2~4문장 + 원문에 나온 사례.
```

Original evidence links available from the source page:
- timestamp → `https://www.youtube.com/watch?v={youtube_id}&t={start}s`
- paragraph → source `url` (text fragment optional)

## keywords/{slug}.md

```yaml
---
slug: pricing
title: 가격 책정
category: pricing
summary: 한 줄 요약 (질문 라우팅에 사용)
reviewed: false           # set true by a human after review
advice: [advice ids used on this page]
images:
  - src: https://i.ytimg.com/vi/.../hqdefault.jpg
    alt: ...
    source: yc-youtube-how-to-price-your-product
updated_at: 2026-09-25
---
자유 형식의 한국어 본문 (가벼운 말투 + 사례).
- 다른 키워드는 [[unit-economics]] 처럼 링크한다.
- 근거는 {{advice:advice_id}} 로 표시한다 → UI가 해당 콘텐츠의 한국어 정리 페이지로 연결한다.
- 도식은 ```mermaid 코드 블록으로 넣는다.
```

## questions/log.jsonl

```json
{"ts": "2026-09-25T10:00:00Z", "question": "...", "matched": ["pricing"], "answered": true,
 "answer": "...", "cited_advice": ["..."], "clicked": null}
```

`answered: false` + empty `matched` = candidate for a new keyword page.

## Content explore (computed by web, not stored)

- The home page content grid (`/#contents`) lists source metadata from `sources/{source_id}.md`.
- Each article's frontmatter `tags` lists 1–4 keyword slugs from `taxonomy.yaml`,
  most central first. `atlas tag-articles --all` sets them: a model reads the
  article and picks keywords; code drops unknown slugs and keeps at most 4.
  Articles already tagged only with known slugs are skipped unless `--force`.
- The home category tabs and keyword chips filter the grid by these tags
  (a category shows contents tagged with any of its keywords). Keywords with no
  tagged contents are hidden. Cards show keyword titles as hashtags. The grid
  sorts by `published`, newest or oldest first; undated sources come last.
- The former `/explore` and `/map` routes redirect to `/#contents`.
