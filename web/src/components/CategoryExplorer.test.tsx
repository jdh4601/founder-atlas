/** @jest-environment jsdom */

import { fireEvent, render, screen } from "@testing-library/react";
import { CategoryExplorer } from "./CategoryExplorer";
import type { CategoryGroup } from "./CategoryExplorer";

const groups: CategoryGroup[] = [
  {
    slug: "pricing",
    title: "가격·수익 모델",
    color: "#8b5cf6",
    keywords: [{ slug: "pricing-strategy", title: "가격 책정" }],
  },
  {
    slug: "sales",
    title: "고객·세일즈",
    color: "#10b981",
    keywords: [{ slug: "first-customers", title: "첫 고객 확보" }],
  },
];

it("shows keywords of the selected category tab only", () => {
  render(<CategoryExplorer groups={groups} />);

  expect(screen.getByRole("link", { name: "가격 책정" })).toHaveAttribute("href", "/k/pricing-strategy");
  expect(screen.queryByRole("link", { name: "첫 고객 확보" })).not.toBeInTheDocument();

  fireEvent.click(screen.getByRole("tab", { name: /고객·세일즈/ }));

  expect(screen.getByRole("link", { name: "첫 고객 확보" })).toBeInTheDocument();
  expect(screen.queryByRole("link", { name: "가격 책정" })).not.toBeInTheDocument();
});
