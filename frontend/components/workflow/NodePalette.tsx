"use client";

import { useCallback } from "react";
import { Bot, Wrench, GitBranch, Timer, Plus } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const nodeTypes = [
  { type: "agent_node", label: "Agent", icon: Bot },
  { type: "tool_node", label: "Tool", icon: Wrench },
  { type: "condition_node", label: "Condition", icon: GitBranch },
  { type: "delay_node", label: "Delay", icon: Timer },
] as const;

export type NodePaletteProps = {
  onAddNode: (nodeType: string) => void;
};

export function NodePalette({ onAddNode }: NodePaletteProps) {
  const handleDragStart = useCallback((e: React.DragEvent, nodeType: string) => {
    e.dataTransfer.setData("application/reactflow-node-type", nodeType);
    e.dataTransfer.effectAllowed = "move";
  }, []);

  return (
    <Card className="border-slate-800 bg-slate-900/50">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base">
          <Plus className="h-4 w-4 text-sky-400" />
          Add Node
        </CardTitle>
        <CardDescription>Drag to canvas or click to add</CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        {nodeTypes.map(({ type, label, icon: Icon }) => (
          <div
            key={type}
            draggable
            onDragStart={(e) => handleDragStart(e, type)}
            onClick={() => onAddNode(type)}
            className="flex cursor-grab items-center gap-3 rounded-xl border border-slate-700/80 bg-slate-800/60 px-3 py-2.5 text-sm text-slate-200 transition-colors hover:border-sky-500/40 hover:bg-slate-800 active:cursor-grabbing"
          >
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-700">
              <Icon className="h-4 w-4 text-sky-400" />
            </div>
            <span className="font-medium">{label}</span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
