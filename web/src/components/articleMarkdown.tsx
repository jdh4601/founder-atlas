/* eslint-disable @next/next/no-img-element */
import type { Components } from "react-markdown";

/** `![alt](src "caption")` becomes a figure; the title is shown as its caption. */
export const articleComponents: Components = {
  h2: ({ children }) => <h2 className="mt-12 text-[24px] font-semibold leading-snug">{children}</h2>,
  p: ({ node, children }) => {
    const onlyChild = node?.children.length === 1 ? node.children[0] : undefined;
    // A lone image is rendered as <figure>, which is not valid inside <p>.
    if (onlyChild?.type === "element" && onlyChild.tagName === "img") return <>{children}</>;
    return <p>{children}</p>;
  },
  img: ({ src, alt, title }) => (
    <figure className="my-10">
      <img
        src={typeof src === "string" ? src : undefined}
        alt={alt ?? ""}
        loading="lazy"
        className="w-full rounded-xl border border-line bg-white"
      />
      {title && (
        <figcaption className="mt-3 text-[13.5px] leading-6 text-ink-muted">{title}</figcaption>
      )}
    </figure>
  ),
};
