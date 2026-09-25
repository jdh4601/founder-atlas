"""Tests for the `atlas` CLI wiring. Network/Claude factories are monkeypatched."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from founder_atlas_pipeline import cli
from test_ingest import FakeWeb, FakeYouTube


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def _args(content_root: Path, *rest: str) -> list[str]:
    return ["--content-dir", str(content_root), *rest]


def test_stats_prints_counts_and_exits_zero(runner: CliRunner, content_root: Path) -> None:
    result = runner.invoke(cli.main, _args(content_root, "stats"))

    assert result.exit_code == 0, result.output
    assert "sources: 0" in result.output


def test_ingest_from_file_reports_each_url(
    runner: CliRunner, content_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli, "make_fetchers", lambda: (FakeYouTube(), FakeWeb()))
    urls = tmp_path / "urls.txt"
    urls.write_text("https://paulgraham.com/ds.html\nhttps://example.com/x\n\n", encoding="utf-8")

    result = runner.invoke(cli.main, _args(content_root, "ingest", "--from-file", str(urls)))

    assert result.exit_code == 0, result.output
    assert "written" in result.output
    assert "failed" in result.output
    assert "1 written, 0 skipped, 1 failed" in result.output


def test_ingest_limit_caps_batch(
    runner: CliRunner, content_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli, "make_fetchers", lambda: (FakeYouTube(), FakeWeb()))
    urls = tmp_path / "urls.txt"
    urls.write_text("https://example.com/a\nhttps://example.com/b\n", encoding="utf-8")

    result = runner.invoke(
        cli.main, _args(content_root, "ingest", "--from-file", str(urls), "--limit", "1")
    )

    assert "0 written, 0 skipped, 1 failed" in result.output


def test_discover_writes_candidates(
    runner: CliRunner, content_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class Lister:
        def list_urls(self, origin: str, limit: int) -> list[str]:
            return ["https://paulgraham.com/ds.html"]

    monkeypatch.setattr(cli, "make_lister", lambda: Lister())

    result = runner.invoke(
        cli.main,
        ["discover", "--origin", "paul-graham", "--candidates-dir", str(tmp_path)],
    )

    assert result.exit_code == 0, result.output
    assert (tmp_path / "paul-graham.txt").read_text(encoding="utf-8").strip() == (
        "https://paulgraham.com/ds.html"
    )


def test_extract_without_api_key_fails_clearly(
    runner: CliRunner, content_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(cli, "load_env", lambda: None)

    result = runner.invoke(cli.main, _args(content_root, "extract", "--all"))

    assert result.exit_code != 0
    assert "ANTHROPIC_API_KEY" in result.output


@pytest.mark.parametrize("provider", ["codex-cli", "claude-code-cli"])
def test_build_pages_cli_provider_does_not_require_api_key(
    runner: CliRunner, content_root: Path, monkeypatch: pytest.MonkeyPatch, provider: str
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(cli, "load_env", lambda: None)

    result = runner.invoke(
        cli.main, _args(content_root, "build-pages", "--provider", provider)
    )

    assert result.exit_code == 0, result.output
    assert "written: 0" in result.output


def test_build_pages_default_still_requires_api_key(
    runner: CliRunner, content_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(cli, "load_env", lambda: None)

    result = runner.invoke(cli.main, _args(content_root, "build-pages"))

    assert result.exit_code != 0
    assert "ANTHROPIC_API_KEY" in result.output
