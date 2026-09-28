/** @jest-environment jsdom */

import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { AskPanel } from "./AskPanel";
import { PREFERENCE_KEYS } from "@/lib/preferences";
import { SHOW_BROWSE_EVENT } from "./BrowseNavLink";

const unansweredResponse = {
  answered: false,
  answer: null,
  matchedPages: [],
  evidence: [],
};

const answeredResponse = {
  answered: true,
  answer: "가격은 높게 시작하세요.",
  matchedPages: [{ slug: "pricing-strategy", title: "가격 책정", summary: "요약" }],
  evidence: [],
};

function mockFetch(body: unknown): jest.Mock {
  const fetchMock = jest.fn().mockResolvedValue({ ok: true, json: async () => body } as Response);
  global.fetch = fetchMock;
  return fetchMock;
}

function ask(text: string): void {
  fireEvent.change(screen.getByRole("textbox", { name: "지금 어떤 문제에 부딪혔나요?" }), {
    target: { value: text },
  });
  fireEvent.click(screen.getByRole("button", { name: "물어보기" }));
}

afterEach(() => {
  delete (global as { fetch?: typeof fetch }).fetch;
  window.localStorage.clear();
});

it.each(["anthropic", "codex-cli", "claude-code-cli"])(
  "sends the %s provider saved in settings",
  async (provider) => {
    window.localStorage.setItem(PREFERENCE_KEYS.askProvider, provider);
    const fetchMock = mockFetch(unansweredResponse);

    render(<AskPanel />);
    ask("  첫 고객은 어떻게 찾나요?  ");

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    expect(JSON.parse(fetchMock.mock.calls[0][1]?.body as string)).toEqual({
      question: "첫 고객은 어떻게 찾나요?",
      provider,
    });
  },
);

it("hides the browse content while answering and restores it on return", async () => {
  mockFetch(answeredResponse);

  render(
    <AskPanel>
      <p>카테고리와 콘텐츠</p>
    </AskPanel>,
  );
  expect(screen.getByText("카테고리와 콘텐츠")).toBeInTheDocument();

  ask("가격은?");

  expect(screen.queryByText("카테고리와 콘텐츠")).not.toBeInTheDocument();
  expect(await screen.findByText("가격은 높게 시작하세요.")).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: /둘러보기로 돌아가기/ }));
  expect(screen.getByText("카테고리와 콘텐츠")).toBeInTheDocument();
  expect(screen.queryByText("가격은 높게 시작하세요.")).not.toBeInTheDocument();
});

it("scopes the question to a keyword page when given one", async () => {
  const fetchMock = mockFetch(unansweredResponse);

  render(<AskPanel keyword="pricing-strategy" />);
  ask("얼마로 시작하나요?");

  await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
  expect(JSON.parse(fetchMock.mock.calls[0][1]?.body as string)).toMatchObject({
    keyword: "pricing-strategy",
  });
});

it("explains a local CLI availability failure without exposing server details", async () => {
  window.localStorage.setItem(PREFERENCE_KEYS.askProvider, "codex-cli");
  global.fetch = jest.fn().mockResolvedValue({ status: 503, ok: false } as Response);

  render(<AskPanel />);
  ask("첫 고객은 어떻게 찾나요?");

  expect(await screen.findByText(/로컬 서버에 CLI가 설치되고 로그인되어 있는지/)).toBeInTheDocument();
});

it("returns to browsing when a header section link asks for it", async () => {
  mockFetch(answeredResponse);

  render(
    <AskPanel>
      <p>카테고리와 콘텐츠</p>
    </AskPanel>,
  );
  ask("가격은?");
  await screen.findByText("가격은 높게 시작하세요.");

  act(() => {
    window.dispatchEvent(new Event(SHOW_BROWSE_EVENT));
  });

  expect(screen.getByText("카테고리와 콘텐츠")).toBeInTheDocument();
});
