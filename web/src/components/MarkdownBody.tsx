import Link from "next/link";
import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import { parseAdviceHref, transformKeywordMarkdown, type TitleLookup } from "@/lib/markdown";
import type { EvidenceEntry } from "@/lib/evidence";
import { InlineEvidenceLink } from "./InlineEvidenceLink";
import { MermaidDiagram } from "./MermaidDiagram";

interface MarkdownBodyProps {
  readonly markdown: string;
  readonly titleFor: TitleLookup;
  readonly evidenceById: ReadonlyMap<string, EvidenceEntry>;
}

/**
 * Renders a keyword page body: `[[slug]]` wikilinks become `/k/slug` links,
 * `{{advice:id}}` markers become evidence chips, and ```mermaid fences
 * render as diagrams client-side.
 */
export function MarkdownBody({ markdown, titleFor, evidenceById }: MarkdownBodyProps) {
  const transformed = transformKeywordMarkdown(markdown, titleFor);
  const components = buildComponents(evidenceById);
  return (
    <div className="prose-body">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {transformed}
      </ReactMarkdown>
    </div>
  );
}

function buildComponents(evidenceById: ReadonlyMap<string, EvidenceEntry>): Components {
  return {
    a: (props) => renderLink(props, evidenceById),
    pre: (props) => <>{props.children}</>,
    code: renderCode,
    p: (props) => <p className="my-3 text-[15px] leading-relaxed text-ink">{props.children}</p>,
    ul: (props) => <ul className="my-3 list-disc pl-5 text-[15px] leading-relaxed">{props.children}</ul>,
    ol: (props) => <ol className="my-3 list-decimal pl-5 text-[15px] leading-relaxed">{props.children}</ol>,
    h1: (props) => <h2 className="mt-8 mb-3 text-[20px] font-semibold">{props.children}</h2>,
    h2: (props) => <h3 className="mt-8 mb-3 text-[18px] font-semibold">{props.children}</h3>,
    h3: (props) => <h4 className="mt-6 mb-2 text-[16px] font-semibold">{props.children}</h4>,
  };
}

interface LinkRendererProps {
  readonly href?: string;
  readonly children?: React.ReactNode;
}

function renderLink(
  { href, children }: LinkRendererProps,
  evidenceById: ReadonlyMap<string, EvidenceEntry>,
) {
  const adviceId = href ? parseAdviceHref(href) : null;
  if (adviceId) {
    const evidence = evidenceById.get(adviceId);
    if (!evidence) return null;
    return <InlineEvidenceLink evidence={evidence} />;
  }
  if (href?.startsWith("/")) {
    return (
      <Link href={href} className="text-focus underline underline-offset-2">
        {children}
      </Link>
    );
  }
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="text-focus underline underline-offset-2"
    >
      {children}
    </a>
  );
}

interface CodeRendererProps {
  readonly className?: string;
  readonly children?: React.ReactNode;
}

function renderCode({ className, children }: CodeRendererProps) {
  const language = /language-(\w+)/.exec(className ?? "")?.[1];
  const code = String(children).replace(/\n$/, "");

  if (language === "mermaid") return <MermaidDiagram code={code} />;
  if (language) {
    return (
      <pre className="my-4 overflow-x-auto rounded-lg border border-line bg-surface p-4 text-[13px]">
        <code>{code}</code>
      </pre>
    );
  }
  return (
    <code className="rounded bg-surface px-1.5 py-0.5 text-[13px] text-ink">
      {children}
    </code>
  );
}
