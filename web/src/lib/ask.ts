import { z } from "zod";
import type { AnthropicJsonClient } from "./anthropicClient";
import type { Advice, KeywordPage } from "./types";

export interface AskResult {
  readonly matched: readonly string[];
  readonly answered: boolean;
  readonly answer: string | null;
  readonly citedAdvice: readonly string[];
}

const MAX_MATCHED_KEYWORDS = 3;

const matchSchema = z.object({ slugs: z.array(z.string()) });
const answerSchema = z.object({
  answer: z.string().min(1),
  citedAdviceIds: z.array(z.string()),
});

const MATCH_SYSTEM_PROMPT = `당신은 창업 조언 아카이브의 라우터입니다.
사용자의 질문을 읽고, 아래 키워드 목록 중 이 질문과 직접 관련된 키워드를 0~3개 고르세요.
관련된 키워드가 없다면 빈 배열을 반환하세요. 목록에 없는 slug를 지어내지 마세요.
반드시 주어진 slug 값 그대로만 사용하세요.`;

const ANSWER_SYSTEM_PROMPT = `당신은 YC/a16z/Paul Graham 조언을 요약해 주는 한국어 어시스턴트입니다.
아래 "근거 조언 목록"에 있는 내용만 근거로 사용해 질문에 2~3문장의 한국어로 답하세요.
목록에 없는 내용을 지어내지 마세요. 답변에서 실제로 근거로 사용한 조언의 id만
citedAdviceIds에 담으세요 (목록에 있는 id만 사용, 지어내지 마세요).`;

/**
 * Answers a question using only the site's advice units (see
 * `docs/content-schema.md` and `docs/design.md`).
 *
 * Step 1: ask Claude which keyword pages (0-3) are relevant, validated
 * against the real set of keyword page slugs.
 * Step 2 (only if step 1 matched something): ask Claude for a short Korean
 * answer grounded only in those pages' advice (claim + body, never
 * `quote`), then drop any cited advice id that doesn't actually exist.
 */
export async function answerQuestion(
  client: AnthropicJsonClient,
  question: string,
  keywordPages: readonly KeywordPage[],
  advice: readonly Advice[],
): Promise<AskResult> {
  const matched = await matchKeywords(client, question, keywordPages);
  if (matched.length === 0) return emptyResult();

  const relevantAdvice = adviceForKeywords(advice, matched);
  if (relevantAdvice.length === 0) return { ...emptyResult(), matched };

  const draft = await draftAnswer(client, question, relevantAdvice);
  if (!draft) return { ...emptyResult(), matched };

  const relevantAdviceIds = new Set(relevantAdvice.map((a) => a.id));
  const citedAdvice = [...new Set(draft.citedAdviceIds)].filter((id) =>
    relevantAdviceIds.has(id),
  );
  if (citedAdvice.length === 0) return { ...emptyResult(), matched };

  return { matched, answered: true, answer: draft.answer, citedAdvice };
}

function emptyResult(): AskResult {
  return { matched: [], answered: false, answer: null, citedAdvice: [] };
}

async function matchKeywords(
  client: AnthropicJsonClient,
  question: string,
  keywordPages: readonly KeywordPage[],
): Promise<string[]> {
  const catalog = keywordPages
    .map((page) => `- ${page.slug}: ${page.title} — ${page.summary}`)
    .join("\n");
  const result = await client.createJson({
    system: MATCH_SYSTEM_PROMPT,
    prompt: `키워드 목록:\n${catalog}\n\n질문: ${question}`,
    schema: matchSchema,
    maxTokens: 256,
  });
  if (!result) return [];

  const validSlugs = new Set(keywordPages.map((page) => page.slug));
  const deduped = [...new Set(result.slugs)].filter((slug) =>
    validSlugs.has(slug),
  );
  return deduped.slice(0, MAX_MATCHED_KEYWORDS);
}

function adviceForKeywords(
  advice: readonly Advice[],
  keywordSlugs: readonly string[],
): Advice[] {
  const bySlug = new Set(keywordSlugs);
  const seen = new Map<string, Advice>();
  for (const unit of advice) {
    if (unit.keywords.some((k) => bySlug.has(k))) seen.set(unit.id, unit);
  }
  return [...seen.values()];
}

async function draftAnswer(
  client: AnthropicJsonClient,
  question: string,
  relevantAdvice: readonly Advice[],
): Promise<{ answer: string; citedAdviceIds: string[] } | null> {
  const catalog = relevantAdvice
    .map((unit) => `- [${unit.id}] ${unit.claim}: ${unit.body}`)
    .join("\n");
  return client.createJson({
    system: ANSWER_SYSTEM_PROMPT,
    prompt: `질문: ${question}\n\n근거 조언 목록:\n${catalog}`,
    schema: answerSchema,
    maxTokens: 1024,
  });
}
