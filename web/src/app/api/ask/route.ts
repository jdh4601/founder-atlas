import { z } from "zod";
import { loadAdvice } from "../../../lib/advice";
import { createAnthropicJsonClient } from "../../../lib/anthropicClient";
import { answerQuestion } from "../../../lib/ask";
import { getContentDir } from "../../../lib/contentDir";
import { loadRepoRootEnv } from "../../../lib/env";
import { loadKeywordPages } from "../../../lib/keywords";
import { appendQuestionLog } from "../../../lib/questionsLog";

const requestSchema = z.object({ question: z.string().min(1) });

/**
 * POST /api/ask — answers a startup-problem question from the site's
 * advice units only (see `docs/content-schema.md` and `docs/design.md`).
 * Every question, matched or not, is appended to
 * `content/questions/log.jsonl`.
 */
export async function POST(request: Request): Promise<Response> {
  loadRepoRootEnv();
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    return jsonResponse(
      { error: "ANTHROPIC_API_KEY is not set" },
      { status: 500 },
    );
  }

  const body = await request.json().catch(() => null);
  const parsed = requestSchema.safeParse(body);
  if (!parsed.success) {
    return jsonResponse({ error: "question is required" }, { status: 400 });
  }
  const question = parsed.data.question;

  const contentDir = getContentDir();
  const keywordPages = loadKeywordPages(contentDir);
  const advice = loadAdvice(contentDir);
  const client = createAnthropicJsonClient(apiKey);

  const result = await answerQuestion(client, question, keywordPages, advice);

  appendQuestionLog(contentDir, {
    ts: new Date().toISOString(),
    question,
    matched: result.matched,
    answered: result.answered,
    answer: result.answer,
    citedAdvice: result.citedAdvice,
    clicked: null,
  });

  return jsonResponse(result, { status: 200 });
}

function jsonResponse(body: unknown, init: { status: number }): Response {
  return new Response(JSON.stringify(body), {
    status: init.status,
    headers: { "content-type": "application/json" },
  });
}
