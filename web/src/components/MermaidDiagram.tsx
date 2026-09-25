"use client";

import { useEffect, useId, useState } from "react";

interface MermaidDiagramProps {
  readonly code: string;
}

/** Renders a ```mermaid code block as an SVG diagram, client-side only. */
export function MermaidDiagram({ code }: MermaidDiagramProps) {
  const id = useId().replace(/[^a-zA-Z0-9]/g, "");
  const [svg, setSvg] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    renderDiagram(id, code)
      .then((result) => {
        if (!cancelled) setSvg(result);
      })
      .catch(() => {
        if (!cancelled) setFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, [id, code]);

  if (failed) return null;
  if (!svg) {
    return (
      <div className="my-4 h-32 animate-pulse rounded-lg border border-line bg-surface" />
    );
  }
  return (
    // mermaid.render() output (from content/ diagram source, not user input)
    <div
      className="my-4 overflow-x-auto rounded-lg border border-line bg-surface p-4"
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}

async function renderDiagram(id: string, code: string): Promise<string> {
  const { default: mermaid } = await import("mermaid");
  mermaid.initialize({ startOnLoad: false, theme: "neutral" });
  const { svg } = await mermaid.render(`mermaid-${id}`, code);
  return svg;
}
