import { z } from "zod";
import { loadAdvice } from "../../../lib/advice";
import { createAnthropicJsonClient } from "../../../lib/anthropicClient";
import { createClaudeCodeCliJsonClient, createCodexCliJsonClient } from "../../../lib/cliClients";
import { answerQuestion } from "../../../lib/ask";
import { buildAskResponse } from "../../../lib/askPresentation";
import { getContentDir } from "../../../lib/contentDir";
import { loadRepoRootEnv } from "../../../lib/env";
import { loadKeywordPages } from "../../../lib/keywords";
import { appendQuestionLog } from "../../../lib/questionsLog";
import { loadSources } from "../../../lib/sources";

export const runtime = "nodejs";

const requestSchema = z.object({
  question: z.string().min(1),
  provider: z.enum(["anthropic", "codex-cli", "claude-code-cli"]).default("anthropic"),
});

/**
 * POST /api/ask — answers a startup-problem question from the site's
 * advice units only (see `docs/content-schema.md` and `docs/design.md`).
 * Every question, matched or not, is appended to
 * `content/questions/log.jsonl`.
 */
export async function POST(request: Request): Promise<Response> {
  loadRepoRootEnv();
  const body = await request.json().catch(() => null);
  const parsed = requestSchema.safeParse(body);
  if (!parsed.success) {
    return jsonResponse({ error: "question is required" }, { status: 400 });
  }
  const question = parsed.data.question;
  const { provider } = parsed.data;

  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (provider === "anthropic" && !apiKey) {
    return jsonResponse(
      { error: "ANTHROPIC_API_KEY is not set" },
      { status: 500 },
    );
  }

  const contentDir = getContentDir();
  const keywordPages = loadKeywordPages(contentDir);
  const advice = loadAdvice(contentDir);
  const sources = loadSources(contentDir);
  const client = provider === "codex-cli"
    ? createCodexCliJsonClient()
    : provider === "claude-code-cli"
      ? createClaudeCodeCliJsonClient()
      : createAnthropicJsonClient(apiKey!);

  let result;
  try {
    result = await answerQuestion(client, question, keywordPages, advice);
  } catch {
    return jsonResponse(
      { error: `${provider} is unavailable or failed to answer` },
      { status: 503 },
    );
  }

  appendQuestionLog(contentDir, {
    ts: new Date().toISOString(),
    question,
    matched: result.matched,
    answered: result.answered,
    answer: result.answer,
    citedAdvice: result.citedAdvice,
    clicked: null,
  });

  const response = buildAskResponse(result, keywordPages, advice, sources);
  return jsonResponse(response, { status: 200 });
}

function jsonResponse(body: unknown, init: { status: number }): Response {
  return new Response(JSON.stringify(body), {
    status: init.status,
    headers: { "content-type": "application/json" },
  });
}
