import { spawn } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { z } from "zod";
import type { AnthropicJsonClient, JsonCompletionRequest } from "./anthropicClient";

const TIMEOUT_MS = 90_000;
const MAX_OUTPUT_BYTES = 1_000_000;

type CliName = "codex" | "claude";

/** Only a validated final assistant message can become an answer. */
export function parseCodexCliJson<T>(output: string, schema: z.ZodType<T>): T | null {
  let finalMessage: string | undefined;
  for (const line of output.split("\n")) {
    if (!line.trim()) continue;
    let event: unknown;
    try {
      event = JSON.parse(line);
    } catch {
      return null;
    }
    if (!isRecord(event) || event.type !== "item.completed") continue;
    const item = event.item;
    if (isRecord(item) && item.type === "agent_message" && typeof item.text === "string") {
      finalMessage = item.text;
    }
  }
  return parseValidatedJson(finalMessage, schema);
}

export function parseClaudeCodeCliJson<T>(output: string, schema: z.ZodType<T>): T | null {
  let envelope: unknown;
  try {
    envelope = JSON.parse(output);
  } catch {
    return null;
  }
  if (!isRecord(envelope) || envelope.is_error === true || envelope.type !== "result") {
    return null;
  }
  const candidate = envelope.structured_output ?? envelope.result;
  return parseValidatedJson(candidate, schema);
}

function parseValidatedJson<T>(value: unknown, schema: z.ZodType<T>): T | null {
  if (typeof value === "string") {
    try {
      value = JSON.parse(value);
    } catch {
      return null;
    }
  }
  const parsed = schema.safeParse(value);
  return parsed.success ? parsed.data : null;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function instruction<T>(request: JsonCompletionRequest<T>): string {
  return `${request.system}\n\n${request.prompt}\n\nReturn only JSON matching the supplied schema. Keep the response within approximately ${request.maxTokens} tokens.`;
}

function runCli(command: CliName, args: string[], input: string, cwd: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd,
      shell: false,
      stdio: ["pipe", "pipe", "pipe"],
      env: { ...process.env, NO_COLOR: "1" },
    });
    let stdout = "";
    let outputBytes = 0;
    let settled = false;
    const fail = (message: string) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      child.kill("SIGKILL");
      reject(new Error(message));
    };
    const timer = setTimeout(() => fail(`${command} CLI timed out`), TIMEOUT_MS);
    child.stdout.on("data", (chunk: Buffer) => {
      outputBytes += chunk.length;
      if (outputBytes > MAX_OUTPUT_BYTES) return fail(`${command} CLI output exceeded limit`);
      stdout += chunk.toString("utf8");
    });
    // Drain diagnostics, but never log them: CLI errors can contain prompts or credentials.
    child.stderr.resume();
    child.on("error", () => fail(`${command} CLI could not start`));
    child.on("close", (code) => {
      clearTimeout(timer);
      if (settled) return;
      settled = true;
      if (code !== 0) reject(new Error(`${command} CLI exited with code ${code}`));
      else resolve(stdout);
    });
    child.stdin.on("error", () => undefined);
    child.stdin.end(input);
  });
}

/** Calls the installed Codex CLI with a disposable session and read-only sandbox. */
export function createCodexCliJsonClient(): AnthropicJsonClient {
  return {
    async createJson<T>(request: JsonCompletionRequest<T>): Promise<T | null> {
      const directory = await mkdtemp(join(tmpdir(), "founder-atlas-codex-"));
      try {
        const schemaPath = join(directory, "output.schema.json");
        await writeFile(schemaPath, JSON.stringify(z.toJSONSchema(request.schema, { target: "draft-07" })), { mode: 0o600 });
        const output = await runCli("codex", [
          "exec", "--json", "--output-schema", schemaPath, "--ephemeral",
          "--sandbox", "read-only", "--ignore-user-config", "--skip-git-repo-check",
          "-C", directory, "-",
        ], instruction(request), directory);
        return parseCodexCliJson(output, request.schema);
      } finally {
        await rm(directory, { recursive: true, force: true });
      }
    },
  };
}

/** Calls Claude Code without tools, MCP servers, or a persisted conversation. */
export function createClaudeCodeCliJsonClient(): AnthropicJsonClient {
  return {
    async createJson<T>(request: JsonCompletionRequest<T>): Promise<T | null> {
      const directory = await mkdtemp(join(tmpdir(), "founder-atlas-claude-"));
      try {
        const output = await runCli("claude", [
          "--print", "--output-format", "json", "--json-schema",
          JSON.stringify(z.toJSONSchema(request.schema, { target: "draft-07" })),
          "--tools", "", "--restricted", "--strict-mcp-config", "--no-session-persistence",
          "--safe-mode", "--permission-mode", "dontAsk", "--permission-prompts", "none",
        ], instruction(request), directory);
        return parseClaudeCodeCliJson(output, request.schema);
      } finally {
        await rm(directory, { recursive: true, force: true });
      }
    },
  };
}
