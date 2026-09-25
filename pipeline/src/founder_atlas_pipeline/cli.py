"""`atlas` command-line entrypoint: discover, ingest, extract, build-pages, stats.

Network and Claude clients are created through the module-level `make_*`
factories so tests can swap them out.
"""

from __future__ import annotations

import os
import sys
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
from founder_atlas_pipeline.stats import collect_stats, format_stats
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


MODEL_PROVIDERS = ("anthropic", "codex-cli", "claude-code-cli")


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


@main.command("build-pages")
@click.option("--keyword", "keyword_slug", default=None, help="Only build this keyword's page.")
@click.option("--force", is_flag=True, help="Also regenerate pages marked reviewed: true.")
@click.option("--provider", type=click.Choice(MODEL_PROVIDERS), default="anthropic", show_default=True)
@click.pass_context
def build_pages_command(ctx: click.Context, keyword_slug: str | None, force: bool, provider: str) -> None:
    """Write content/keywords/{slug}.md from advice units."""
    _prepare_provider(provider)
    from founder_atlas_pipeline.build_pages.client import CLIPageWriterClient, ClaudePageWriterClient
    from founder_atlas_pipeline.build_pages.pipeline import build_pages
    from founder_atlas_pipeline.cli_providers import CLIProviderError

    content = _content_dir(ctx)
    taxonomy = load_taxonomy(content / "taxonomy.yaml")
    client = ClaudePageWriterClient() if provider == "anthropic" else CLIPageWriterClient(provider)
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
