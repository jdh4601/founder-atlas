import Anthropic from "@anthropic-ai/sdk";
import { zodOutputFormat } from "@anthropic-ai/sdk/helpers/zod";
import type { z } from "zod";

/** The Haiku model used for both `/api/ask` steps (classify, then answer). */
export const ASK_MODEL = "claude-haiku-4-5-20251001";

export interface JsonCompletionRequest<T> {
  readonly system: string;
  readonly prompt: string;
  readonly schema: z.ZodType<T>;
  readonly maxTokens: number;
}

/**
 * A minimal, injectable interface over "ask Claude for JSON matching a Zod
 * schema". `lib/ask.ts` depends only on this, so tests can supply a mock
 * without touching the real Anthropic SDK or network.
 */
export interface AnthropicJsonClient {
  createJson<T>(request: JsonCompletionRequest<T>): Promise<T | null>;
}

/** Wraps the real Anthropic SDK client behind `AnthropicJsonClient`. */
export function createAnthropicJsonClient(apiKey: string): AnthropicJsonClient {
  const client = new Anthropic({ apiKey });
  return {
    async createJson<T>(request: JsonCompletionRequest<T>): Promise<T | null> {
      const response = await client.messages.parse({
        model: ASK_MODEL,
        max_tokens: request.maxTokens,
        system: request.system,
        messages: [{ role: "user", content: request.prompt }],
        output_config: { format: zodOutputFormat(request.schema) },
      });
      return response.parsed_output;
    },
  };
}
