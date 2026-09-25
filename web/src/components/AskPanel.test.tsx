/** @jest-environment jsdom */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { AskPanel } from "./AskPanel";

const askResponse = {
  answered: false,
  answer: null,
  matchedPages: [],
  evidence: [],
};

afterEach(() => {
  delete (global as { fetch?: typeof fetch }).fetch;
});

it.each([
  ["Anthropic API (API 키 필요)", "anthropic"],
  ["Codex CLI (로컬 서버)", "codex-cli"],
  ["Claude Code CLI (로컬 서버)", "claude-code-cli"],
])("sends the selected %s provider", async (label, provider) => {
  const fetchMock = jest.fn().mockResolvedValue({
    ok: true,
    json: async () => askResponse,
  } as Response);
  global.fetch = fetchMock;

  render(<AskPanel />);
  fireEvent.change(screen.getByRole("combobox", { name: "응답 모델 연결" }), {
    target: { value: provider },
  });
  fireEvent.change(screen.getByRole("textbox", { name: "지금 어떤 문제에 부딪혔나요?" }), {
    target: { value: "  첫 고객은 어떻게 찾나요?  " },
  });
  fireEvent.click(screen.getByRole("button", { name: "물어보기" }));

  await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
  expect(JSON.parse(fetchMock.mock.calls[0][1]?.body as string)).toEqual({
    question: "첫 고객은 어떻게 찾나요?",
    provider,
  });
  if (provider !== "anthropic") {
    expect(screen.getByText(/로컬 서버에서만 사용할 수 있어요/)).toBeInTheDocument();
  }
  expect(screen.getByRole("option", { name: label })).toBeInTheDocument();
});

it("explains a local CLI availability failure without exposing server details", async () => {
  global.fetch = jest.fn().mockResolvedValue({ status: 503, ok: false } as Response);

  render(<AskPanel />);
  fireEvent.change(screen.getByRole("combobox", { name: "응답 모델 연결" }), {
    target: { value: "codex-cli" },
  });
  fireEvent.change(screen.getByRole("textbox", { name: "지금 어떤 문제에 부딪혔나요?" }), {
    target: { value: "첫 고객은 어떻게 찾나요?" },
  });
  fireEvent.click(screen.getByRole("button", { name: "물어보기" }));

  expect(await screen.findByText(/로컬 서버에 CLI가 설치되고 로그인되어 있는지/)).toBeInTheDocument();
});
