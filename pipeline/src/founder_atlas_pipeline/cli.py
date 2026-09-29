"""`atlas` command-line entrypoint: discover, ingest, extract, build-pages, stats.

Network and Claude clients are created through the module-level `make_*`
factories so tests can swap them out.
"""

from __future__ import annotations

import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import click
from dotenv import load_dotenv

from founder_atlas_pipeline.advice import list_advice_ids
from founder_atlas_pipeline.discover import CandidateLister, WebCandidateLister, discover
from founder_atlas_pipeline.ingest.fetchers import (
    TrafilaturaWebFetcher,
    WebFetcher,
    YouTubeFetcher,
    YtDlpYouTubeFetcher,
)
from founder_atlas_pipeline.ingest.pipeline import ORIGINS, ingest_many
from founder_atlas_pipeline.paths import find_repo_root
from founder_atlas_pipeline.sources import list_source_ids
from founder_atlas_pipeline.source_articles import CLIArticleWriter, generate_article
from founder_atlas_pipeline.source_tldrs import missing_tldr_paths, write_tldr_batch
from founder_atlas_pipeline.stats import collect_stats, format_stats
from founder_atlas_pipeline.tagging import CLITagger, tag_article
from founder_atlas_pipeline.taxonomy import load_taxonomy


def load_env() -> None:
    """Load `ANTHROPIC_API_KEY` etc. from the repo-root `.env`, if present."""
    load_dotenv(find_repo_root() / ".env")


def make_fetchers() -> tuple[YouTubeFetcher, WebFetcher]:
    """Create the real network fetchers used by `ingest`."""
    return YtDlpYouTubeFetcher(), TrafilaturaWebFetcher()


def make_lister() -> CandidateLister:
    """Create the real candidate lister used by `discover`."""
    return WebCandidateLister()


def _require_api_key() -> None:
    load_env()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise click.ClickException(
            "ANTHROPIC_API_KEY is not set. Add it to the repo-root .env (see .env.example)."
        )


MODEL_PROVIDERS = ("anthropic", "codex-cli", "claude-code-cli", "template")


def _prepare_provider(provider: str) -> None:
    """Load .env for API calls; local CLI providers use their own login state."""
    if provider == "anthropic":
        _require_api_key()


def _content_dir(ctx: click.Context) -> Path:
    explicit: Path | None = ctx.obj.get("content_dir")
    return explicit or find_repo_root() / "content"


@click.group()
@click.option(
    "--content-dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=None,
    help="content/ directory (default: <repo root>/content).",
)
@click.pass_context
def main(ctx: click.Context, content_dir: Path | None) -> None:
    """Founder Atlas content pipeline."""
    ctx.ensure_object(dict)
    ctx.obj["content_dir"] = content_dir


@main.command("discover")
@click.option("--origin", type=click.Choice(ORIGINS), required=True)
@click.option("--limit", type=int, default=50, show_default=True)
@click.option(
    "--candidates-dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=None,
    help="Where {origin}.txt is written (default: pipeline/candidates).",
)
def discover_command(origin: str, limit: int, candidates_dir: Path | None) -> None:
    """List real candidate URLs for ORIGIN into candidates/{origin}.txt."""
    target = candidates_dir or find_repo_root() / "pipeline" / "candidates"
    added = discover(origin, limit, candidates_dir=target, lister=make_lister())
    click.echo(f"{added} new URL(s) added to {target / f'{origin}.txt'}")


def _read_url_file(path: Path) -> list[str]:
    lines = (line.strip() for line in path.read_text(encoding="utf-8").splitlines())
    return [line for line in lines if line and not line.startswith("#")]


@main.command("ingest")
@click.argument("url", required=False)
@click.option("--from-file", type=click.Path(dir_okay=False, exists=True, path_type=Path))
@click.option("--limit", type=int, default=None, help="Max URLs to take from --from-file.")
@click.option("--origin", type=click.Choice(ORIGINS), default=None, help="Origin for YouTube URLs.")
@click.option("--force", is_flag=True, help="Overwrite already-ingested sources.")
@click.pass_context
def ingest_command(
    ctx: click.Context,
    url: str | None,
    from_file: Path | None,
    limit: int | None,
    origin: str | None,
    force: bool,
) -> None:
    """Fetch URL (or every URL in --from-file) into content/sources/."""
    urls = [url] if url else _read_url_file(from_file) if from_file else []
    if not urls:
        raise click.UsageError("Give a URL or --from-file.")
    youtube, web = make_fetchers()
    outcomes = ingest_many(
        _content_dir(ctx), urls[:limit], youtube=youtube, web=web, origin=origin, force=force
    )
    for outcome in outcomes:
        detail = outcome.source_id or outcome.error
        click.echo(f"[{outcome.status}] {outcome.url} -> {detail}")
    counts = {
        status: sum(1 for o in outcomes if o.status == status)
        for status in ("written", "skipped", "failed")
    }
    click.echo(
        f"{counts['written']} written, {counts['skipped']} skipped, {counts['failed']} failed"
    )


@main.command("extract")
@click.argument("source_id", required=False)
@click.option("--all", "extract_all", is_flag=True, help="Every source without advice yet.")
@click.option("--provider", type=click.Choice(MODEL_PROVIDERS), default="anthropic", show_default=True)
@click.pass_context
def extract_command(ctx: click.Context, source_id: str | None, extract_all: bool, provider: str) -> None:
    """Extract and verify advice units for SOURCE_ID (or --all)."""
    _prepare_provider(provider)
    from founder_atlas_pipeline.extract.client import CLIExtractClient, ClaudeExtractClient
    from founder_atlas_pipeline.extract.pipeline import extract_source
    from founder_atlas_pipeline.cli_providers import CLIProviderError

    content = _content_dir(ctx)
    targets = _extract_targets(content, source_id, extract_all)
    taxonomy = load_taxonomy(content / "taxonomy.yaml")
    client = ClaudeExtractClient() if provider == "anthropic" else CLIExtractClient(provider)
    for target in targets:
        try:
            stats = extract_source(content, target, taxonomy, client)
        except CLIProviderError as exc:
            raise click.ClickException(str(exc)) from exc
        click.echo(
            f"{target}: {stats.written}/{stats.total_candidates} written "
            f"(dropped: {stats.dropped_low_score} low score, "
            f"{stats.dropped_invalid_taxonomy} invalid taxonomy, "
            f"{stats.dropped_duplicate_quote} duplicate quote)"
        )


def _extract_targets(content: Path, source_id: str | None, extract_all: bool) -> list[str]:
    if source_id:
        return [source_id]
    if not extract_all:
        raise click.UsageError("Give a SOURCE_ID or --all.")
    # Re-extracting a source would append duplicate advice, so --all only
    # picks sources that have none yet.
    return [s for s in list_source_ids(content) if not list_advice_ids(content, s)]


@main.command("write-source-articles")
@click.argument("source_id", required=False)
@click.option("--all", "write_all", is_flag=True, help="Write every ingested source article.")
@click.option("--force", is_flag=True, help="Regenerate existing articles.")
@click.option("--jobs", type=click.IntRange(1, 8), default=1, show_default=True)
@click.option("--provider", type=click.Choice(("codex-cli", "claude-code-cli")), default="codex-cli")
@click.pass_context
def write_source_articles_command(
    ctx: click.Context, source_id: str | None, write_all: bool, force: bool, jobs: int, provider: str
) -> None:
    """Turn raw source text into a grounded Korean reading article."""
    if not source_id and not write_all:
        raise click.UsageError("Give a SOURCE_ID or --all.")
    content = _content_dir(ctx)
    targets = [source_id] if source_id else list_source_ids(content)
    writer = CLIArticleWriter(provider)
    counts = {"written": 0, "skipped": 0, "failed": 0}
    def run_one(target: str):
        try:
            return target, generate_article(content, target, writer, force=force), None
        except Exception as exc:
            return target, None, exc

    with ThreadPoolExecutor(max_workers=jobs) as executor:
        futures = [executor.submit(run_one, target) for target in targets]
        for future in as_completed(futures):
            target, result, exc = future.result()
            if exc is not None:
                counts["failed"] += 1
                click.echo(f"[failed] {target}: {exc}", err=True)
                continue
            assert result is not None
            counts[result.status] += 1
            click.echo(f"[{result.status}] {target}")
    click.echo(", ".join(f"{status}: {count}" for status, count in counts.items()))
    if counts["failed"]:
        sys.exit(1)


@main.command("import-insights")
@click.argument("vault_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--folder", default="07_Insights", show_default=True, help="Notes folder inside the vault.")
@click.option("--force", is_flag=True, help="Re-import notes that were already imported.")
@click.option("--jobs", type=click.IntRange(1, 8), default=1, show_default=True)
@click.option("--provider", type=click.Choice(("codex-cli", "claude-code-cli")), default="claude-code-cli")
@click.pass_context
def import_insights_command(
    ctx: click.Context, vault_dir: Path, folder: str, force: bool, jobs: int, provider: str
) -> None:
    """Import Obsidian insight notes as `insights-*` sources with Korean articles."""
    from founder_atlas_pipeline.insights import (
        AnyLanguageTranscripts,
        CLIInsightWriter,
        import_insight_note,
        load_excluded_ids,
        note_ids,
        youtube_thumbnail,
    )

    content = _content_dir(ctx)
    notes = sorted((vault_dir / folder).glob("*.md"))
    writer = CLIInsightWriter(provider)
    taxonomy = load_taxonomy(content / "taxonomy.yaml")
    tagger = CLITagger(provider)
    transcripts = AnyLanguageTranscripts()
    counts = {"written": 0, "skipped": 0, "failed": 0}

    def run_one(note: Path, source_id: str):
        try:
            result = import_insight_note(
                content, vault_dir, note, writer, youtube=transcripts,
                thumbnail_for=youtube_thumbnail, source_id=source_id, force=force,
            )
            if result.status == "written":
                tag_article(content, result.source_id, taxonomy, tagger, force=True)
            return note, result, None
        except Exception as exc:
            return note, None, exc

    with ThreadPoolExecutor(max_workers=jobs) as executor:
        futures = [executor.submit(run_one, note, source_id) for note, source_id in note_ids(notes, load_excluded_ids(content))]
        for future in as_completed(futures):
            note, result, exc = future.result()
            if exc is not None:
                counts["failed"] += 1
                click.echo(f"[failed] {note.name}: {exc}", err=True)
                continue
            assert result is not None
            counts[result.status] += 1
            click.echo(f"[{result.status}] {result.source_id} <- {note.name}")
    click.echo(", ".join(f"{status}: {count}" for status, count in counts.items()))
    if counts["failed"]:
        sys.exit(1)


@main.command("tag-articles")
@click.argument("source_id", required=False)
@click.option("--all", "tag_all", is_flag=True, help="Tag every source article.")
@click.option("--force", is_flag=True, help="Retag articles that already have keyword tags.")
@click.option("--jobs", type=click.IntRange(1, 8), default=1, show_default=True)
@click.option("--provider", type=click.Choice(("codex-cli", "claude-code-cli")), default="claude-code-cli")
@click.pass_context
def tag_articles_command(
    ctx: click.Context, source_id: str | None, tag_all: bool, force: bool, jobs: int, provider: str
) -> None:
    """Set each article's `tags` to the taxonomy keyword slugs it covers."""
    if not source_id and not tag_all:
        raise click.UsageError("Give a SOURCE_ID or --all.")
    content = _content_dir(ctx)
    taxonomy = load_taxonomy(content / "taxonomy.yaml")
    targets = [source_id] if source_id else sorted(p.stem for p in (content / "source_articles").glob("*.md"))
    tagger = CLITagger(provider)
    counts = {"tagged": 0, "skipped": 0, "failed": 0}

    def run_one(target: str):
        try:
            return target, tag_article(content, target, taxonomy, tagger, force=force), None
        except Exception as exc:
            return target, None, exc

    with ThreadPoolExecutor(max_workers=jobs) as executor:
        futures = [executor.submit(run_one, target) for target in targets]
        for future in as_completed(futures):
            target, result, exc = future.result()
            if exc is not None:
                counts["failed"] += 1
                click.echo(f"[failed] {target}: {exc}", err=True)
                continue
            assert result is not None
            counts[result.status] += 1
            click.echo(f"[{result.status}] {target}: {', '.join(result.tags)}")
    click.echo(", ".join(f"{status}: {count}" for status, count in counts.items()))
    if counts["failed"]:
        sys.exit(1)


@main.command("add-figures")
@click.argument("source_id", required=False)
@click.option("--all", "add_all", is_flag=True, help="Add figures to every source article.")
@click.option("--force", is_flag=True, help="Replace figures an article already has.")
@click.option(
    "--recapture-frames", is_flag=True, help="Only re-capture existing video frames at the same timestamps."
)
@click.option("--jobs", type=click.IntRange(1, 8), default=1, show_default=True)
@click.option("--provider", type=click.Choice(("codex-cli", "claude-code-cli")), default="codex-cli")
@click.pass_context
def add_figures_command(
    ctx: click.Context,
    source_id: str | None,
    add_all: bool,
    force: bool,
    recapture_frames: bool,
    jobs: int,
    provider: str,
) -> None:
    """Place video frames or original post images inside Korean source articles."""
    from founder_atlas_pipeline.figures import (
        ARTICLE_SCHEMA,
        ARTICLE_SYSTEM_PROMPT,
        VIDEO_SCHEMA,
        VIDEO_SYSTEM_PROMPT,
        CLIFigurePlanner,
        CLIFramePicker,
        FigureResult,
        add_figures_to_source,
        capture_youtube_frame,
        fetch_page_html,
    )
    from founder_atlas_pipeline.figures import recapture_frames as recapture
    from founder_atlas_pipeline.figure_search import (
        CHOOSE_SCHEMA,
        CHOOSE_SYSTEM_PROMPT,
        PICK_SCHEMA,
        PICK_SYSTEM_PROMPT,
        CLIImageReviewer,
        download_image,
        plan_search_figures,
        search_bing_images,
    )
    from founder_atlas_pipeline.source_articles import article_path
    from founder_atlas_pipeline.sources import read_source

    if not source_id and not add_all:
        raise click.UsageError("Give a SOURCE_ID or --all.")
    content = _content_dir(ctx)
    public_dir = content.parent / "web" / "public"
    targets = [source_id] if source_id else [
        target for target in list_source_ids(content) if article_path(content, target).is_file()
    ]
    video_planner = CLIFigurePlanner(provider, VIDEO_SYSTEM_PROMPT, VIDEO_SCHEMA)
    article_planner = CLIFigurePlanner(provider, ARTICLE_SYSTEM_PROMPT, ARTICLE_SCHEMA)
    pick_planner = CLIFigurePlanner(provider, PICK_SYSTEM_PROMPT, PICK_SCHEMA)
    choose_planner = CLIFigurePlanner(provider, CHOOSE_SYSTEM_PROMPT, CHOOSE_SCHEMA)
    counts = {"written": 0, "partial": 0, "skipped": 0, "no-figures": 0, "failed": 0}

    frame_picker = CLIFramePicker(provider)

    def capture(video_id: str, start: int, output: Path) -> None:
        capture_youtube_frame(video_id, start, output, frame_picker)

    def run_one(target: str):
        try:
            is_video = read_source(content, target).format == "video"
            if recapture_frames:
                count = recapture(content, public_dir, target, capture) if is_video else 0
                return target, FigureResult(target, "written" if count else "skipped", count), None
            result = add_figures_to_source(
                content,
                public_dir,
                target,
                video_planner if is_video else article_planner,
                capture_frame=capture,
                fetch_html=fetch_page_html,
                search_figures=lambda body, count: plan_search_figures(
                    body,
                    target,
                    pick_planner,
                    CLIImageReviewer(provider),
                    chooser=choose_planner,
                    search=search_bing_images,
                    download=download_image,
                    public_dir=public_dir,
                    count=count,
                ),
                force=force,
            )
            return target, result, None
        except Exception as exc:
            return target, None, exc

    with ThreadPoolExecutor(max_workers=jobs) as executor:
        futures = [executor.submit(run_one, target) for target in targets]
        for future in as_completed(futures):
            target, result, exc = future.result()
            if exc is not None:
                counts["failed"] += 1
                click.echo(f"[failed] {target}: {exc}", err=True)
                continue
            assert result is not None
            counts[result.status] += 1
            click.echo(f"[{result.status}] {target} ({result.count})")
    click.echo(", ".join(f"{status}: {count}" for status, count in counts.items()))
    if counts["failed"]:
        sys.exit(1)


@main.command("write-source-tldrs")
@click.option("--jobs", type=click.IntRange(1, 4), default=2, show_default=True)
@click.option("--provider", type=click.Choice(("codex-cli", "claude-code-cli")), default="codex-cli")
@click.pass_context
def write_source_tldrs_command(ctx: click.Context, jobs: int, provider: str) -> None:
    """Add one-sentence takeaways to existing source articles."""
    paths = missing_tldr_paths(_content_dir(ctx))
    batches = [paths[index : index + 10] for index in range(0, len(paths), 10)]
    failures = 0
    with ThreadPoolExecutor(max_workers=jobs) as executor:
        futures = {executor.submit(write_tldr_batch, batch, provider): batch for batch in batches}
        for future in as_completed(futures):
            batch = futures[future]
            try:
                completed = future.result()
            except Exception as exc:
                failures += len(batch)
                click.echo(f"[failed] {batch[0].stem}…{batch[-1].stem}: {exc}", err=True)
            else:
                click.echo(f"[written] {len(completed)} one-line summaries")
    click.echo(f"written: {len(paths) - failures}, failed: {failures}")
    if failures:
        sys.exit(1)


@main.command("build-pages")
@click.option("--keyword", "keyword_slug", default=None, help="Only build this keyword's page.")
@click.option("--force", is_flag=True, help="Also regenerate pages marked reviewed: true.")
@click.option("--provider", type=click.Choice(MODEL_PROVIDERS), default="anthropic", show_default=True)
@click.pass_context
def build_pages_command(ctx: click.Context, keyword_slug: str | None, force: bool, provider: str) -> None:
    """Write content/keywords/{slug}.md from advice units."""
    _prepare_provider(provider)
    from founder_atlas_pipeline.build_pages.client import (
        CLIPageWriterClient,
        ClaudePageWriterClient,
        TemplatePageWriterClient,
    )
    from founder_atlas_pipeline.build_pages.pipeline import build_pages
    from founder_atlas_pipeline.cli_providers import CLIProviderError

    content = _content_dir(ctx)
    taxonomy = load_taxonomy(content / "taxonomy.yaml")
    if provider == "anthropic":
        client = ClaudePageWriterClient()
    elif provider == "template":
        client = TemplatePageWriterClient()
    else:
        client = CLIPageWriterClient(provider)
    try:
        stats = build_pages(content, taxonomy, client, keyword_slug=keyword_slug, force=force)
    except CLIProviderError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(
        f"written: {len(stats.written)}, preserved (reviewed): "
        f"{len(stats.preserved_reviewed)}, skipped (no advice): {stats.skipped_no_advice}"
    )


@main.command("stats")
@click.pass_context
def stats_command(ctx: click.Context) -> None:
    """Show counts and check the 20-keywords-per-category cap."""
    stats = collect_stats(_content_dir(ctx))
    click.echo(format_stats(stats))
    if stats.has_errors:
        sys.exit(1)
