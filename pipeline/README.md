# founder-atlas pipeline

Python CLI (`atlas`) that turns source URLs into schema-conformant Markdown under
`content/`. Data contract: `../docs/content-schema.md`.

## Setup

```bash
cd pipeline
uv sync
cp ../.env.example ../.env   # set ANTHROPIC_API_KEY when using the default Anthropic API provider
```

## Commands

```bash
# 1. List real candidate URLs → pipeline/candidates/{origin}.txt (no API key needed)
uv run atlas discover --origin yc-youtube --limit 50
uv run atlas discover --origin lightcone --limit 30   # YC channel search; review the list
uv run atlas discover --origin paul-graham --limit 50
uv run atlas discover --origin a16z --limit 50        # from post-sitemap.xml (RSS is 404)

# 2. Fetch metadata + raw text → content/sources/ (no API key needed)
uv run atlas ingest https://paulgraham.com/ds.html
uv run atlas ingest --from-file candidates/paul-graham.txt --limit 25
uv run atlas ingest --from-file candidates/lightcone.txt --origin lightcone

# 3. Extract advice, verify quotes (rapidfuzz >= 90), compute anchors by code
uv run atlas extract --all          # only sources that have no advice yet
uv run atlas extract <source_id>
uv run atlas extract --all --provider codex-cli
uv run atlas extract --all --provider claude-code-cli

# 4. Write keyword pages (reviewed: true pages are preserved unless --force)
uv run atlas build-pages
uv run atlas build-pages --keyword pricing-strategy
uv run atlas build-pages --provider codex-cli
uv run atlas build-pages --provider claude-code-cli
uv run atlas build-pages --provider template  # offline evidence-led drafts

# 5. Counts + 20-keywords-per-category check (exit 1 on violation)
uv run atlas stats

# 6. Translate and organize every stored source into Korean reading articles
uv run atlas write-source-articles --all --jobs 4
uv run atlas write-source-articles <source_id> --force
uv run atlas write-source-tldrs  # add one-line takeaways to older articles

# 7. Import Obsidian insight notes (07_Insights) as `insights-*` sources
uv run atlas import-insights ~/Obsidian-vault --jobs 3

# 8. Put 2-5 figures inside each Korean article (needs yt-dlp, ffmpeg, a model CLI)
uv run atlas add-figures --all --jobs 3
uv run atlas add-figures <source_id> --force  # replace an article's figures
uv run atlas add-figures --all --recapture-frames --provider claude-code-cli  # re-pick clearer frames
```

Edit a candidates file before ingesting: delete lines you don't want, `#` comments are ignored.

## Notes

- `ingest` leaves `title_ko` and the Korean summary empty so collection works
  without an API key. The web app falls back to the original title.
- YouTube can't tell YC from Lightcone by URL; pass `--origin lightcone` for those.
- Failed URLs (e.g. no English transcript) are reported and the batch continues.
- `add-figures`: videos get frames captured at timestamps computed from a
  model-chosen transcript quote (fuzzy match >= 90), saved to
  `web/public/figures/{source_id}/`. Blog posts get every original body image
  (`wp-image-*`). Essays, and posts with fewer than 2 original images, are
  topped up by Bing image search; the model CLI looks at each downloaded candidate,
  keeps only relevant ones, and captions what it actually shows. `--all`
  skips articles that already contain figures.
- `--all` skips sources that already have advice. A direct re-extract skips
  already stored quotes; delete a source's advice files to regenerate them.
- `extract` and `build-pages` default to the Anthropic API and require
  `ANTHROPIC_API_KEY`. The `codex-cli` and `claude-code-cli` providers use the
  respective installed CLI's existing login, with no API key in `.env`.
  Install and sign in to the chosen CLI before running either command.

## Tests

```bash
uv run pytest -x -q   # no network, no Claude calls
```
