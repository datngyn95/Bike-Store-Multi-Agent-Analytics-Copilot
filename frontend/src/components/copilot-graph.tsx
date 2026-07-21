import type { CopilotResponse } from "@/lib/api";

type GraphEvidence = CopilotResponse["graph"];
type GraphNode = GraphEvidence["nodes"][number];

type PositionedNode = GraphNode & {
  x: number;
  y: number;
};

const laneTypes = [
  ["project", "schema", "report"],
  ["agent"],
  ["question_example", "sql_template"],
  ["metric"],
  ["table", "view", "metadata_table"]
];

const typeLabels: Record<string, string> = {
  agent: "agent",
  metadata_table: "metadata",
  metric: "metric",
  project: "project",
  question_example: "question",
  report: "report",
  schema: "schema",
  sql_template: "template",
  table: "table",
  view: "view"
};

function laneForType(type: string): number {
  const lane = laneTypes.findIndex((types) => types.includes(type));
  return lane >= 0 ? lane : laneTypes.length - 1;
}

function truncateLabel(label: string, maxLength = 30): string {
  return label.length > maxLength ? `${label.slice(0, maxLength - 1)}...` : label;
}

function layoutNodes(nodes: GraphNode[]): { nodes: PositionedNode[]; width: number; height: number } {
  const lanes = laneTypes.map(() => [] as GraphNode[]);
  for (const node of nodes) {
    lanes[laneForType(node.type)].push(node);
  }

  const maxLaneSize = Math.max(1, ...lanes.map((lane) => lane.length));
  const width = 1080;
  const height = Math.max(360, 96 + maxLaneSize * 74);
  const laneWidth = width / lanes.length;
  const positioned: PositionedNode[] = [];

  lanes.forEach((lane, laneIndex) => {
    const gap = height / (lane.length + 1 || 2);
    lane.forEach((node, nodeIndex) => {
      positioned.push({
        ...node,
        x: laneWidth * laneIndex + laneWidth / 2,
        y: gap * (nodeIndex + 1)
      });
    });
  });

  return { nodes: positioned, width, height };
}

export function CopilotGraph({ graph }: { graph?: GraphEvidence }) {
  const safeGraph = graph ?? { nodes: [], edges: [] };

  if (!safeGraph.nodes.length) {
    return <div className="empty-state">No graph evidence returned for this question.</div>;
  }

  const { nodes, width, height } = layoutNodes(safeGraph.nodes);
  const nodeById = new Map(nodes.map((node) => [node.id, node]));
  const edges = safeGraph.edges
    .map((edge) => ({ ...edge, sourceNode: nodeById.get(edge.source), targetNode: nodeById.get(edge.target) }))
    .filter((edge) => edge.sourceNode && edge.targetNode);

  return (
    <div className="copilot-graph">
      <svg aria-label="Graph RAG evidence" role="img" viewBox={`0 0 ${width} ${height}`}>
        <defs>
          <marker id="graph-arrow" markerHeight="8" markerWidth="8" orient="auto" refX="7" refY="3.5">
            <path d="M0,0 L7,3.5 L0,7 Z" />
          </marker>
        </defs>
        <g className="graph-edges">
          {edges.map((edge, index) => {
            const source = edge.sourceNode as PositionedNode;
            const target = edge.targetNode as PositionedNode;
            return (
              <path
                d={`M ${source.x + 74} ${source.y} C ${(source.x + target.x) / 2} ${source.y}, ${(source.x + target.x) / 2} ${target.y}, ${target.x - 74} ${target.y}`}
                key={`${edge.source}-${edge.target}-${edge.type}-${index}`}
              >
                <title>{`${edge.source} --${edge.type}--> ${edge.target}`}</title>
              </path>
            );
          })}
        </g>
        <g className="graph-nodes">
          {nodes.map((node) => (
            <g className={`graph-node ${node.matched ? "matched" : ""}`} key={node.id} transform={`translate(${node.x - 74} ${node.y - 25})`}>
              <title>{[node.label, node.description, node.source].filter(Boolean).join("\n")}</title>
              <rect height="50" rx="8" width="148" />
              <text className="graph-node-label" x="12" y="22">
                {truncateLabel(node.label)}
              </text>
              <text className="graph-node-type" x="12" y="38">
                {typeLabels[node.type] ?? node.type}
              </text>
            </g>
          ))}
        </g>
      </svg>
      <div className="graph-legend">
        <span className="source-pill">{safeGraph.nodes.length} nodes</span>
        <span className="source-pill">{safeGraph.edges.length} edges</span>
        <span className="source-pill">{safeGraph.nodes.filter((node) => node.matched).length} retrieved</span>
      </div>
    </div>
  );
}
