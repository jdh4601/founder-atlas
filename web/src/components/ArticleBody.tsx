import ReactMarkdown from "react-markdown";
import { articleComponents } from "./articleMarkdown";

interface ArticleBodyProps {
  readonly markdown: string;
}

/** Korean source article body (see `content/source_articles/`). */
export function ArticleBody({ markdown }: ArticleBodyProps) {
  return (
    <div className="space-y-5 text-[16px] leading-8 text-ink">
      <ReactMarkdown components={articleComponents}>{markdown}</ReactMarkdown>
    </div>
  );
}
