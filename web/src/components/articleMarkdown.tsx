/* eslint-disable @next/next/no-img-element */
import type { Components } from "react-markdown";

/** `![alt](src "caption")` becomes a figure; the title is shown as its caption. */
export const articleComponents: Components = {
  h2: ({ children }) => <h2 className="mt-12 text-[24px] font-semibold leading-snug">{children}</h2>,
  h3: ({ children }) => <h3 className="mt-8 text-[19px] font-semibold leading-snug">{children}</h3>,
  ul: ({ children }) => <ul className="list-disc space-y-2 pl-6 marker:text-ink-muted">{children}</ul>,
  ol: ({ children }) => <ol className="list-decimal space-y-2 pl-6 marker:text-ink-muted">{children}</ol>,
  li: ({ children }) => <li className="pl-1">{children}</li>,
  strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
  blockquote: ({ children }) => (
    <blockquote className="border-l-2 border-focus bg-surface px-5 py-3 font-medium [&>p]:m-0">
      {children}
    </blockquote>
  ),
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
