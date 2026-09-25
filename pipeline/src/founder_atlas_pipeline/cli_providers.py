"""Run authenticated local model CLIs for structured generation.

The caller supplies all context through stdin. Each invocation starts in an
empty temporary directory, so repository instructions and source files are not
implicitly available to the model process.
"""

from __future__ import annotations

import json
import os
import selectors
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

CLI_TIMEOUT_SECONDS = 180
CLI_MAX_OUTPUT_BYTES = 2_000_000


class CLIProviderError(RuntimeError):
    """A local CLI could not produce the requested structured response."""


def _communicate_bounded(argv: list[str], prompt: str, cwd: Path) -> tuple[bytes, bytes]:
    """Feed stdin and capture pipes with strict time and combined byte limits."""
    try:
        process = subprocess.Popen(
            argv,
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        raise CLIProviderError(f"{argv[0]} CLI is not installed or not on PATH") from exc

    assert process.stdin and process.stdout and process.stderr
    stream_input = memoryview(prompt.encode("utf-8"))
    output = {process.stdout: bytearray(), process.stderr: bytearray()}
    selector = selectors.DefaultSelector()
    for stream in (process.stdin, process.stdout, process.stderr):
        os.set_blocking(stream.fileno(), False)
    selector.register(process.stdin, selectors.EVENT_WRITE)
    selector.register(process.stdout, selectors.EVENT_READ)
    selector.register(process.stderr, selectors.EVENT_READ)
    deadline = time.monotonic() + CLI_TIMEOUT_SECONDS
    input_offset = 0
    try:
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise CLIProviderError(f"{argv[0]} CLI timed out after {CLI_TIMEOUT_SECONDS}s")
            for key, _ in selector.select(timeout=remaining):
                stream = key.fileobj
                if stream is process.stdin:
                    try:
                        sent = os.write(stream.fileno(), stream_input[input_offset : input_offset + 65536])
                    except BrokenPipeError:
                        sent = 0
                        input_offset = len(stream_input)
                    input_offset += sent
                    if input_offset >= len(stream_input):
                        selector.unregister(stream)
                        stream.close()
                else:
                    data = os.read(stream.fileno(), 65536)
                    if not data:
                        selector.unregister(stream)
                        stream.close()
                        continue
                    output[stream].extend(data)
                    if sum(len(part) for part in output.values()) > CLI_MAX_OUTPUT_BYTES:
                        raise CLIProviderError(f"{argv[0]} CLI output exceeded {CLI_MAX_OUTPUT_BYTES} bytes")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise CLIProviderError(f"{argv[0]} CLI timed out after {CLI_TIMEOUT_SECONDS}s")
        process.wait(timeout=remaining)
        if process.returncode:
            # CLI stderr may contain prompts, source text, or credentials.
            if argv[0] == "claude":
                try:
                    envelope = json.loads(output[process.stdout])
                except (json.JSONDecodeError, TypeError):
                    envelope = {}
                if isinstance(envelope, dict) and envelope.get("api_error_status") == 429:
                    raise CLIProviderError("claude-code-cli session limit reached")
            raise CLIProviderError(f"{argv[0]} CLI exited with status {process.returncode}")
        return bytes(output[process.stdout]), bytes(output[process.stderr])
    except subprocess.TimeoutExpired as exc:
        raise CLIProviderError(f"{argv[0]} CLI timed out after {CLI_TIMEOUT_SECONDS}s") from exc
    finally:
        selector.close()
        if process.poll() is None:
            process.kill()
        process.wait()


def _json_object(raw: str, provider: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        raise CLIProviderError(f"{provider} returned invalid JSON") from exc
    if not isinstance(payload, dict):
        raise CLIProviderError(f"{provider} returned JSON that is not an object")
    return payload


def _validate(value: Any, schema: dict[str, Any], provider: str) -> None:
    """Check the JSON Schema subset used by this pipeline's two responses."""
    kinds = schema.get("type", [])
    if isinstance(kinds, str):
        kinds = [kinds]
    matching = (
        ("object" in kinds and isinstance(value, dict))
        or ("array" in kinds and isinstance(value, list))
        or ("string" in kinds and isinstance(value, str))
        or ("null" in kinds and value is None)
    )
    if not matching:
        raise CLIProviderError(f"{provider} response does not match the expected schema")
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        if not set(schema.get("required", [])) <= value.keys():
            raise CLIProviderError(f"{provider} response is missing a required field")
        if schema.get("additionalProperties") is False and not value.keys() <= properties.keys():
            raise CLIProviderError(f"{provider} response has an unexpected field")
        for name, item in value.items():
            if name in properties:
                _validate(item, properties[name], provider)
    elif isinstance(value, list):
        for item in value:
            _validate(item, schema["items"], provider)


def run_structured_cli(
    provider: str, *, system_prompt: str, user_prompt: str, schema: dict
) -> dict[str, Any]:
    """Return a JSON object from Codex or Claude Code's existing local login.

    No API key is required by this adapter. Both CLIs receive only the prompt
    supplied here and have no writable project workspace. Claude's tools are
    disabled; Codex runs with a read-only sandbox in an empty directory.
    """
    executable = {"codex-cli": "codex", "claude-code-cli": "claude"}.get(provider)
    if executable is None:
        raise ValueError(f"Unknown CLI provider: {provider}")
    if shutil.which(executable) is None:
        raise CLIProviderError(f"{executable} CLI is not installed or not on PATH")

    prompt = f"{system_prompt}\n\n{user_prompt}\n\nReturn only JSON matching the supplied schema."
    with tempfile.TemporaryDirectory(prefix="atlas-model-") as temp:
        workdir = Path(temp)
        if provider == "codex-cli":
            schema_file = workdir / "schema.json"
            result_file = workdir / "result.json"
            schema_file.write_text(json.dumps(schema, ensure_ascii=False), encoding="utf-8")
            argv = [
                executable,
                "exec",
                "--skip-git-repo-check",
                "--ephemeral",
                "--ignore-user-config",
                "--ignore-rules",
                "--sandbox",
                "read-only",
                "--output-schema",
                str(schema_file),
                "--output-last-message",
                str(result_file),
                "-",
            ]
            _communicate_bounded(argv, prompt, workdir)
            try:
                if result_file.stat().st_size > CLI_MAX_OUTPUT_BYTES:
                    raise CLIProviderError("codex-cli response exceeded the output limit")
                result = _json_object(result_file.read_text(encoding="utf-8"), provider)
            except FileNotFoundError as exc:
                raise CLIProviderError("codex-cli did not write a response") from exc
            _validate(result, schema, provider)
            return result

        argv = [
            executable,
            "--print",
            "--safe-mode",
            "--restricted",
            "--strict-mcp-config",
            "--tools",
            "",
            "--permission-mode",
            "dontAsk",
            "--permission-prompts",
            "none",
            "--no-session-persistence",
            "--output-format",
            "json",
            "--json-schema",
            json.dumps(schema, ensure_ascii=False),
        ]
        stdout, _ = _communicate_bounded(argv, prompt, workdir)
        envelope = _json_object(stdout.decode("utf-8"), provider)
        if envelope.get("is_error"):
            raise CLIProviderError("claude-code-cli reported an error")
        structured = envelope.get("structured_output")
        if structured is not None:
            if not isinstance(structured, dict):
                raise CLIProviderError("claude-code-cli returned invalid structured output")
            _validate(structured, schema, provider)
            return structured
        result = envelope.get("result")
        payload = _json_object(result, provider)
        _validate(payload, schema, provider)
        return payload
