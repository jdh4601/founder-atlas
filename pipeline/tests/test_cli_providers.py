"""Local CLI adapter tests; no model invocation or network traffic."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from founder_atlas_pipeline import cli_providers
from founder_atlas_pipeline.extract.client import CLIExtractClient


SCHEMA = {
    "type": "object",
    "properties": {"answer": {"type": "string"}},
    "required": ["answer"],
    "additionalProperties": False,
}


def test_codex_cli_uses_isolated_cwd_stdin_and_schema(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli_providers.shutil, "which", lambda name: f"/usr/bin/{name}")
    seen = {}

    def fake_run(argv: list[str], prompt: str, cwd: Path) -> tuple[bytes, bytes]:
        schema_path = Path(argv[argv.index("--output-schema") + 1])
        seen.update(argv=argv, prompt=prompt, cwd=cwd, schema=json.loads(schema_path.read_text()))
        Path(argv[argv.index("--output-last-message") + 1]).write_text(
            '{"answer":"좋아요"}', encoding="utf-8"
        )
        return b"", b""

    monkeypatch.setattr(cli_providers, "_communicate_bounded", fake_run)
    result = cli_providers.run_structured_cli(
        "codex-cli", system_prompt="system", user_prompt="source text", schema=SCHEMA
    )

    assert result == {"answer": "좋아요"}
    assert seen["argv"][-1] == "-"
    assert "--sandbox" in seen["argv"]
    assert "read-only" in seen["argv"]
    assert "source text" in seen["prompt"]
    assert "source text" not in " ".join(seen["argv"])
    assert seen["schema"] == SCHEMA
    assert not seen["cwd"].exists()


def test_claude_code_cli_reads_structured_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli_providers.shutil, "which", lambda name: f"/usr/bin/{name}")
    seen = {}

    def fake_run(argv: list[str], prompt: str, cwd: Path) -> tuple[bytes, bytes]:
        seen.update(argv=argv, prompt=prompt)
        return b'{"is_error":false,"structured_output":{"answer":"ok"}}', b""

    monkeypatch.setattr(cli_providers, "_communicate_bounded", fake_run)
    assert cli_providers.run_structured_cli(
        "claude-code-cli", system_prompt="system", user_prompt="data", schema=SCHEMA
    ) == {"answer": "ok"}
    assert "--safe-mode" in seen["argv"]
    assert "--restricted" in seen["argv"]
    assert seen["argv"][seen["argv"].index("--permission-mode") + 1] == "dontAsk"
    assert "--tools" in seen["argv"]
    assert "data" not in " ".join(seen["argv"])


def test_cli_schema_rejects_bad_candidate_without_echoing_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli_providers.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(
        cli_providers,
        "_communicate_bounded",
        lambda argv, prompt, cwd: (b'{"structured_output":{"candidates":[{"quote":"secret"}]}}', b""),
    )
    with pytest.raises(cli_providers.CLIProviderError) as error:
        CLIExtractClient("claude-code-cli").extract_candidates(
            "private transcript",
            source_title="Title",
            speakers=[],
            category_slugs=["pricing"],
            keyword_slugs=["pricing-strategy"],
        )
    assert "secret" not in str(error.value)
    assert "private transcript" not in str(error.value)


def test_missing_cli_has_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli_providers.shutil, "which", lambda name: None)
    with pytest.raises(cli_providers.CLIProviderError, match="not installed"):
        cli_providers.run_structured_cli(
            "codex-cli", system_prompt="s", user_prompt="u", schema=SCHEMA
        )
