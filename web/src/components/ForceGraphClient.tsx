"use client";

import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";
import { useCallback } from "react";
import type { NodeObject } from "react-force-graph-2d";
import type { Graph } from "@/lib/types";

const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), {
  ssr: false,
});

interface ForceGraphClientProps {
  readonly graph: Graph;
}

/** The keyword map: nodes sized by advice count, colored by category. */
export function ForceGraphClient({ graph }: ForceGraphClientProps) {
  const router = useRouter();

  const handleNodeClick = useCallback(
    (node: NodeObject) => {
      if (typeof node.id === "string") router.push(`/k/${node.id}`);
    },
    [router],
  );

  const graphData = {
    nodes: graph.nodes.map((node) => ({ ...node, id: node.slug })),
    links: graph.edges.map((edge) => ({
      source: edge.source,
      target: edge.target,
      value: edge.weight,
    })),
  };

  return (
    <div className="h-[calc(100vh-160px)] w-full">
      <ForceGraph2D
        graphData={graphData}
        nodeId="id"
        nodeLabel="title"
        nodeVal={(node) => 2 + (node as { adviceCount: number }).adviceCount}
        nodeColor={(node) => (node as { color: string }).color}
        linkColor={() => "rgba(148, 153, 160, 0.35)"}
        linkWidth={(link) => Math.min(4, 1 + (link as { value: number }).value * 0.5)}
        backgroundColor="transparent"
        onNodeClick={handleNodeClick}
      />
    </div>
  );
}
