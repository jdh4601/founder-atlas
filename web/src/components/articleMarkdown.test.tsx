/** @jest-environment jsdom */

import type { ComponentProps, ReactElement } from "react";
import { render, screen } from "@testing-library/react";
import { articleComponents } from "./articleMarkdown";

type Renderer = (props: Record<string, unknown>) => ReactElement;
const Img = articleComponents.img as unknown as Renderer;
const P = articleComponents.p as unknown as Renderer;

function imageNode() {
  return { type: "element", tagName: "img", properties: {}, children: [] };
}

it("renders a markdown image as a lazy figure with its title as caption", () => {
  const { container } = render(
    <Img src="https://example.com/chart.jpg" alt="세 구간 리텐션 곡선" title="리텐션 곡선. 출처: a16z" />,
  );

  const image = screen.getByRole("img", { name: "세 구간 리텐션 곡선" });
  expect(image).toHaveAttribute("src", "https://example.com/chart.jpg");
  expect(image).toHaveAttribute("loading", "lazy");
  expect(image.closest("figure")).not.toBeNull();
  expect(container.querySelector("figcaption")).toHaveTextContent("리텐션 곡선. 출처: a16z");
});

it("omits the caption when the image has no title", () => {
  const { container } = render(<Img src="https://example.com/a.jpg" alt="그림" />);
  expect(container.querySelector("figcaption")).toBeNull();
});

it("does not wrap a lone image in a paragraph", () => {
  const { container } = render(
    <P node={{ type: "element", tagName: "p", children: [imageNode()] }}>
      <span>그림</span>
    </P>,
  );
  expect(container.querySelector("p")).toBeNull();
});

it("keeps ordinary text in a paragraph", () => {
  const props: ComponentProps<"p"> & { node: unknown } = {
    node: { type: "element", tagName: "p", children: [{ type: "text", value: "문단" }] },
    children: "문단",
  };
  const { container } = render(<P {...props} />);
  expect(container.querySelector("p")).toHaveTextContent("문단");
});

it.each(["ul", "ol", "li", "blockquote", "h3", "strong"] as const)("styles markdown %s", (tag) => {
  expect(articleComponents[tag]).toBeDefined();
});

it("renders a blockquote as a highlighted aside", () => {
  const Blockquote = articleComponents.blockquote as unknown as Renderer;
  const { container } = render(<Blockquote>새길 문장</Blockquote>);
  expect(container.querySelector("blockquote")).toHaveClass("border-l-2");
});
