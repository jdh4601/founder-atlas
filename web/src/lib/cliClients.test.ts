import { z } from "zod";
import { parseClaudeCodeCliJson, parseCodexCliJson } from "./cliClients";

const schema = z.object({ answer: z.string().min(1), citedAdviceIds: z.array(z.string()) });
const valid = { answer: "근거가 있습니다.", citedAdviceIds: ["advice-1"] };

describe("Codex CLI JSON output", () => {
  it("takes the last completed agent message and validates it", () => {
    const output = [
      JSON.stringify({ type: "item.completed", item: { type: "command_execution", text: JSON.stringify(valid) } }),
      JSON.stringify({ type: "item.completed", item: { type: "agent_message", text: JSON.stringify({ answer: "draft", citedAdviceIds: [] }) } }),
      JSON.stringify({ type: "item.completed", item: { type: "agent_message", text: JSON.stringify(valid) } }),
      JSON.stringify({ type: "turn.completed" }),
    ].join("\n");
    expect(parseCodexCliJson(output, schema)).toEqual(valid);
  });

  it("rejects malformed JSONL and invalid final shape", () => {
    expect(parseCodexCliJson("not JSON", schema)).toBeNull();
    expect(parseCodexCliJson(JSON.stringify({ type: "item.completed", item: { type: "agent_message", text: '{"answer":""}' } }), schema)).toBeNull();
  });
});

describe("Claude Code CLI JSON output", () => {
  it("accepts structured_output and validates it", () => {
    expect(parseClaudeCodeCliJson(JSON.stringify({ type: "result", structured_output: valid }), schema)).toEqual(valid);
  });

  it("accepts a JSON result string and rejects errors or invalid output", () => {
    expect(parseClaudeCodeCliJson(JSON.stringify({ type: "result", result: JSON.stringify(valid) }), schema)).toEqual(valid);
    expect(parseClaudeCodeCliJson(JSON.stringify({ type: "result", is_error: true, structured_output: valid }), schema)).toBeNull();
    expect(parseClaudeCodeCliJson(JSON.stringify({ type: "result", structured_output: { answer: 3, citedAdviceIds: [] } }), schema)).toBeNull();
  });
});
