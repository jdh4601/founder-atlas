/** @jest-environment jsdom */

import { fireEvent, render, screen } from "@testing-library/react";
import { SettingsMenu } from "./SettingsMenu";
import { PREFERENCE_KEYS } from "@/lib/preferences";

afterEach(() => {
  window.localStorage.clear();
  delete document.documentElement.dataset.theme;
});

it("applies and remembers the chosen color theme", () => {
  render(<SettingsMenu />);
  fireEvent.click(screen.getByRole("button", { name: "설정" }));

  fireEvent.click(screen.getByRole("radio", { name: "라이트" }));
  expect(document.documentElement.dataset.theme).toBe("light");
  expect(window.localStorage.getItem(PREFERENCE_KEYS.theme)).toBe("light");

  fireEvent.click(screen.getByRole("radio", { name: "시스템" }));
  expect(document.documentElement.dataset.theme).toBeUndefined();
});

it("remembers the answer model selection", () => {
  render(<SettingsMenu />);
  fireEvent.click(screen.getByRole("button", { name: "설정" }));

  fireEvent.change(screen.getByRole("combobox", { name: "응답 모델" }), {
    target: { value: "claude-code-cli" },
  });

  expect(window.localStorage.getItem(PREFERENCE_KEYS.askProvider)).toBe("claude-code-cli");
  expect(screen.getByText(/로컬 서버에서만 사용할 수 있어요/)).toBeInTheDocument();
});
