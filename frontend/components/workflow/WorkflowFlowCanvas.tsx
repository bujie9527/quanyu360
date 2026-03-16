"use client";

import {
  ReactFlow,
  Controls,
  Background,
  applyNodeChanges,
  applyEdgeChanges,
  addEdge,
  Handle,
  Position,
  type Node,
  type Edge,
  type Connection,
  type OnNodesChange,
  type OnEdgesChange,
  type NodeProps,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useCallback } from "react";
import { Bot, Wrench, GitBranch, Timer } from "lucide-react";

const nodeTypes = ["agent_node", "tool_node", "condition_node", "delay_node"] as const;

const iconMap: Record<string, typeof Bot> = {
  agent_node: Bot,
  tool_node: Wrench,
  condition_node: GitBranch,
  delay_node: Timer,
};

const labelMap: Record<string, string> = {
  agent_node: "Agent",
  tool_node: "Tool",
  condition_node: "Condition",
  delay_node: "Delay",
};

function WorkflowNode({ data, type, selected }: NodeProps) {
  const nodeType = (type as string) || (data?.nodeType as string) || "agent_node";
  const Icon = iconMap[nodeType] ?? Bot;
  const label = (data?.label as string) || (data?.name as string) || labelMap[nodeType] || "Node";

  return (
    <div
      className={`min-w-[160px] rounded-xl border-2 px-4 py-3 shadow-lg transition-all ${
        selected
          ? "border-sky-500 bg-slate-800/95"
          : "border-slate-600 bg-slate-900/90 hover:border-slate-500"
      }`}
    >
      <Handle type="target" position={Position.Top} className="!h-2 !w-2 !border-2 !border-sky-500 !bg-slate-900" />
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-700/80">
          <Icon className="h-4 w-4 text-sky-400" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate font-medium text-slate-100">{label}</p>
          <p className="truncate text-xs text-slate-400">{nodeType.replace("_node", "")}</p>
        </div>
      </div>
      <Handle type="source" position={Position.Bottom} className="!h-2 !w-2 !border-2 !border-sky-500 !bg-slate-900" />
    </div>
  );
}

const nodeTypeMap = {
  agent_node: WorkflowNode,
  tool_node: WorkflowNode,
  condition_node: WorkflowNode,
  delay_node: WorkflowNode,
  default: WorkflowNode,
};

export type WorkflowFlowCanvasProps = {
  nodes: Node[];
  edges: Edge[];
  onNodesChange: (nodes: Node[]) => void;
  onEdgesChange: (edges: Edge[]) => void;
  onNodeSelect?: (node: Node | null) => void;
  readOnly?: boolean;
};

export function WorkflowFlowCanvas({
  nodes,
  edges,
  onNodesChange: onNodesChangeProp,
  onEdgesChange: onEdgesChangeProp,
  onNodeSelect,
  readOnly = false,
}: WorkflowFlowCanvasProps) {
  const handleNodesChange: OnNodesChange = useCallback(
    (changes) => {
      onNodesChangeProp(applyNodeChanges(changes, nodes));
    },
    [nodes, onNodesChangeProp]
  );

  const handleEdgesChange: OnEdgesChange = useCallback(
    (changes) => {
      onEdgesChangeProp(applyEdgeChanges(changes, edges));
    },
    [edges, onEdgesChangeProp]
  );

  const handleConnect = useCallback(
    (params: Connection) => {
      onEdgesChangeProp(addEdge(params, edges));
    },
    [edges, onEdgesChangeProp]
  );

  const handleNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      onNodeSelect?.(node);
    },
    [onNodeSelect]
  );

  const handlePaneClick = useCallback(() => {
    onNodeSelect?.(null);
  }, [onNodeSelect]);

  return (
    <div className="h-full w-full rounded-xl border border-slate-800 bg-slate-950">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={handleNodesChange}
        onEdgesChange={handleEdgesChange}
        onConnect={readOnly ? undefined : handleConnect}
        onNodeClick={handleNodeClick}
        onPaneClick={handlePaneClick}
        nodeTypes={nodeTypeMap}
        nodesDraggable={!readOnly}
        nodesConnectable={!readOnly}
        elementsSelectable={!readOnly}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        className="bg-slate-950"
        defaultEdgeOptions={{
          type: "smoothstep",
          style: { stroke: "rgb(56 189 248 / 0.5)" },
          animated: false,
        }}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="rgb(51 65 85)" gap={16} />
        <Controls className="!border-slate-700 !bg-slate-900/90 !shadow-lg" showInteractive={false} />
      </ReactFlow>
    </div>
  );
}

export { nodeTypes, labelMap, iconMap };
