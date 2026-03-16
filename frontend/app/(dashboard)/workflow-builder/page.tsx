"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { Node, Edge } from "@xyflow/react";
import { useCallback, useEffect, useState } from "react";
import { Play, Save, Trash2 } from "lucide-react";

import { NodeConfigPanel } from "@/components/workflow/NodeConfigPanel";
import { NodePalette } from "@/components/workflow/NodePalette";
import { WorkflowFlowCanvas } from "@/components/workflow/WorkflowFlowCanvas";
import { HeroTip, PageHero, selectClassName } from "@/components/shared/admin-kit";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  createWorkflowFromBuilder,
  getWorkflowBuilder,
  listProjects,
  listWorkflows,
  runWorkflow,
  updateWorkflowStatus,
  type WorkflowBuilderDetail,
} from "@/lib/api";

let nodeId = 0;
function generateId() {
  return `node_${++nodeId}`;
}

function flowToBuilderFormat(nodes: Node[], edges: Edge[]) {
  return {
    nodes: nodes.map((n) => ({
      id: n.id,
      type: n.type || "agent_node",
      data: n.data || {},
      position: n.position,
    })),
    edges: edges.map((e) => ({
      source: e.source,
      target: e.target,
      sourceHandle: e.sourceHandle ?? null,
      targetHandle: e.targetHandle ?? null,
    })),
  };
}

function builderToFlowFormat(builder: WorkflowBuilderDetail): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = (builder.nodes || []).map((n) => ({
    id: n.id,
    type: (n.type as string) || "agent_node",
    position: n.position || { x: 0, y: 0 },
    data: { ...n.data, label: n.data?.name ?? n.id, name: n.data?.name ?? n.id },
  }));
  const edges: Edge[] = (builder.edges || []).map((e, i) => ({
    id: e.id || `e${i}`,
    source: e.source,
    target: e.target,
  }));
  return { nodes, edges };
}

export default function WorkflowBuilderPage() {
  const queryClient = useQueryClient();
  const [projectId, setProjectId] = useState("");
  const [workflowName, setWorkflowName] = useState("新建流程");
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string | null>(null);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);

  const projectsQuery = useQuery({ queryKey: ["projects"], queryFn: () => listProjects() });
  const defaultProjectId = projectsQuery.data?.[0]?.id ?? "";
  const effectiveProjectId = projectId || defaultProjectId;

  const workflowsQuery = useQuery({
    queryKey: ["workflows", effectiveProjectId],
    queryFn: () => listWorkflows({ project_id: effectiveProjectId }),
    enabled: !!effectiveProjectId,
  });
  const workflowDetailQuery = useQuery({
    queryKey: ["workflow-builder", selectedWorkflowId],
    queryFn: () => getWorkflowBuilder(selectedWorkflowId!),
    enabled: !!selectedWorkflowId,
  });
  const agentsQuery = useQuery({
    queryKey: ["agents", effectiveProjectId],
    queryFn: async () => {
      const { listAgents } = await import("@/lib/api");
      return listAgents({ project_id: effectiveProjectId });
    },
    enabled: !!effectiveProjectId,
  });

  const createMutation = useMutation({
    mutationFn: createWorkflowFromBuilder,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflows"] });
    },
  });

  const runMutation = useMutation({
    mutationFn: async (payload: { workflow_id: string; input_payload?: Record<string, unknown> }) => {
      await updateWorkflowStatus(payload.workflow_id, "active");
      queryClient.invalidateQueries({ queryKey: ["workflows"] });
      return runWorkflow(payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["executions"] });
    },
  });

  const handleAddNode = useCallback((nodeType: string) => {
    const id = generateId();
    setNodes((nds) => [
      ...nds,
      {
        id,
        type: nodeType,
        position: { x: 250 + nds.length * 30, y: 100 + nds.length * 30 },
        data: { label: nodeType.replace("_node", ""), name: "" },
      },
    ]);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      const nodeType = e.dataTransfer.getData("application/reactflow-node-type");
      if (nodeType) handleAddNode(nodeType);
    },
    [handleAddNode]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
  }, []);

  const handleNodeUpdate = useCallback((nodeId: string, data: Record<string, unknown>) => {
    setNodes((nds) =>
      nds.map((n) => (n.id === nodeId ? { ...n, data: { ...n.data, ...data } } : n))
    );
    if (selectedNode?.id === nodeId) {
      setSelectedNode((prev) => (prev ? { ...prev, data: { ...prev.data, ...data } } : null));
    }
  }, [selectedNode?.id]);

  const handleSave = useCallback(
    (activate = false) => {
      const { nodes: n, edges: e } = flowToBuilderFormat(nodes, edges);
      createMutation.mutate({
        project_id: effectiveProjectId,
        name: workflowName,
        status: activate ? "active" : "draft",
        nodes: n,
        edges: e,
        configuration: { trigger_type: "manual", entry_node_id: n[0]?.id ?? null },
      });
    },
    [nodes, edges, effectiveProjectId, workflowName, createMutation]
  );

  const handleRun = useCallback(() => {
    if (!selectedWorkflowId) return;
    runMutation.mutate({ workflow_id: selectedWorkflowId, input_payload: {} });
  }, [selectedWorkflowId, runMutation]);

  useEffect(() => {
    const data = workflowDetailQuery.data;
    if (data && selectedWorkflowId && (data.nodes?.length ?? 0) > 0) {
      const { nodes: n, edges: e } = builderToFlowFormat(data);
      setNodes(n);
      setEdges(e);
    }
  }, [selectedWorkflowId, workflowDetailQuery.data]);

  return (
    <div className="space-y-6">
      <PageHero
        eyebrow="流程编排"
        title="可视化流程构建器"
        description="拖拽节点、连接边、配置参数，构建自动化执行流程。"
      >
        <HeroTip label="节点类型" value="Agent、工具、条件、延时。" />
        <HeroTip label="执行" value="保存并激活后即可运行流程。" />
      </PageHero>

      <div className="grid gap-6 xl:grid-cols-[240px_1fr_320px]">
        <div className="space-y-4">
          <Card className="border-slate-800 bg-slate-900/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-base">项目</CardTitle>
              <CardDescription>选择流程所属项目</CardDescription>
            </CardHeader>
            <CardContent>
              <select
                className={selectClassName}
                value={effectiveProjectId}
                onChange={(e) => setProjectId(e.target.value)}
              >
                {(projectsQuery.data ?? []).map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </CardContent>
          </Card>
          <NodePalette onAddNode={handleAddNode} />
        </div>

        <div
          className="flex min-h-[500px] flex-col gap-4"
          onDrop={handleDrop}
          onDragOver={handleDragOver}
        >
          <div className="flex flex-wrap items-center gap-3">
            <Input
              value={workflowName}
              onChange={(e) => setWorkflowName(e.target.value)}
              placeholder="流程名称"
              className="max-w-[240px]"
            />
            <Button onClick={() => handleSave()} disabled={createMutation.isPending || !nodes.length}>
              <Save className="mr-2 h-4 w-4" />
              {createMutation.isPending ? "保存中..." : "保存流程"}
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                setNodes([]);
                setEdges([]);
                setSelectedWorkflowId(null);
                setSelectedNode(null);
              }}
            >
              <Trash2 className="mr-2 h-4 w-4" />
              清空画布
            </Button>
          </div>
          <div className="min-h-[450px] flex-1 rounded-xl border border-slate-800 bg-slate-950">
            <WorkflowFlowCanvas
              nodes={nodes}
              edges={edges}
              onNodesChange={setNodes}
              onEdgesChange={setEdges}
              onNodeSelect={setSelectedNode}
            />
          </div>
        </div>

        <div className="space-y-4">
          <NodeConfigPanel
            node={selectedNode}
            agents={(agentsQuery.data ?? []).map((a) => ({ id: a.id, name: a.name }))}
            onUpdate={handleNodeUpdate}
          />
          <Card className="border-slate-800 bg-slate-900/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-base">运行流程</CardTitle>
              <CardDescription>选择已保存的流程并执行</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <select
                className={selectClassName}
                value={selectedWorkflowId ?? ""}
                onChange={(e) => {
                  const id = e.target.value || null;
                  setSelectedWorkflowId(id);
                  if (id) {
                    queryClient.invalidateQueries({ queryKey: ["workflow-builder", id] });
                  }
                }}
              >
                <option value="">选择流程</option>
                {(workflowsQuery.data ?? []).map((w) => (
                  <option key={w.id} value={w.id}>
                    {w.name}
                  </option>
                ))}
              </select>
              <Button
                className="w-full"
                disabled={!selectedWorkflowId || runMutation.isPending}
                onClick={handleRun}
              >
                <Play className="mr-2 h-4 w-4" />
                {runMutation.isPending ? "执行中..." : "执行流程"}
              </Button>
              {runMutation.data && (
                <p className="text-xs text-slate-400">
                  执行 ID: {runMutation.data.execution_id}
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
