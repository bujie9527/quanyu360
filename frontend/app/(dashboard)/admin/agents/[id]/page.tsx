"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, BookOpen, Loader2 } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import {
  PanelHeader,
  PageHero,
  TableShell,
} from "@/components/shared/admin-kit";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  getAgentInstance,
  listProjectKnowledgeBases,
  updateAgentInstance,
} from "@/lib/api-admin";

export default function AdminAgentDetailPage() {
  const params = useParams();
  const queryClient = useQueryClient();
  const id = params?.id as string;

  const NONE_VALUE = "__none__";
  const [kbId, setKbId] = useState<string>(NONE_VALUE);

  const agentQuery = useQuery({
    queryKey: ["admin-agent-instance", id],
    queryFn: () => getAgentInstance(id),
    enabled: !!id,
  });

  const agent = agentQuery.data;
  const projectId = agent?.project_id;

  useEffect(() => {
    if (agent) {
      setKbId(agent.knowledge_base_id ?? NONE_VALUE);
    }
  }, [agent?.knowledge_base_id, agent]);

  const kbsQuery = useQuery({
    queryKey: ["project-knowledge-bases", projectId],
    queryFn: () => listProjectKnowledgeBases(projectId!),
    enabled: !!projectId,
  });

  const updateMutation = useMutation({
    mutationFn: (payload: { knowledge_base_id: string | null }) =>
      updateAgentInstance(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-agent-instance", id] });
      queryClient.invalidateQueries({ queryKey: ["admin-agent-instances"] });
    },
  });

  const kbs = kbsQuery.data ?? [];
  const hasKbs = kbs.length > 0;
  const validKbValues = [NONE_VALUE, ...kbs.map((kb) => kb.id)];

  const handleSave = () => {
    const currentKbId = kbId || agent?.knowledge_base_id || NONE_VALUE;
    const toSave =
      currentKbId === NONE_VALUE || !validKbValues.includes(currentKbId)
        ? null
        : currentKbId;
    updateMutation.mutate({ knowledge_base_id: toSave });
  };

  if (!id) {
    return (
      <div className="space-y-6">
        <p className="text-slate-400">无效的 Agent ID</p>
        <Link href="/admin/agents">
          <Button variant="outline">返回列表</Button>
        </Link>
      </div>
    );
  }

  if (agentQuery.isLoading || !agent) {
    return (
      <div className="flex min-h-[200px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-slate-500" />
      </div>
    );
  }

  const currentKbId = kbId || agent.knowledge_base_id || NONE_VALUE;
  const safeSelectValue = validKbValues.includes(currentKbId) ? currentKbId : NONE_VALUE;

  return (
    <div className="space-y-6">
      <Link
        href="/admin/agents"
        className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-slate-200"
      >
        <ArrowLeft className="h-4 w-4" />
        返回 Agent 列表
      </Link>

      <PageHero
        eyebrow="AI员工 · Agent 详情"
        title={agent.name}
        description={`模板: ${agent.template_name ?? "-"} · 项目: ${agent.project_name ?? "-"} · 模型: ${agent.model ?? "-"}`}
      />

      <TableShell>
        <div className="p-6 space-y-6">
          <PanelHeader
            title="KnowledgeBase 绑定"
            description="选择知识库后，AgentRuntime 将自动加载该知识库用于 RAG 检索。"
          />

          <div className="flex flex-wrap items-end gap-4">
            <div className="min-w-[280px] space-y-2">
              <label className="text-sm font-medium text-slate-300">
                知识库
              </label>
              <Select
                value={safeSelectValue}
                onValueChange={(v) => setKbId(v)}
                disabled={!hasKbs || updateMutation.isPending}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder={hasKbs ? "选择知识库…" : "该项目暂无知识库"} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={NONE_VALUE}>不绑定</SelectItem>
                  {kbs.map((kb) => (
                    <SelectItem key={kb.id} value={kb.id}>
                      {kb.name}
                      {kb.slug ? ` (${kb.slug})` : ""}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {!hasKbs && (
                <p className="text-xs text-slate-500">
                  请先在项目空间创建知识库
                </p>
              )}
            </div>
            <Button
              onClick={handleSave}
              disabled={
                updateMutation.isPending ||
                (safeSelectValue === NONE_VALUE ? null : safeSelectValue) ===
                  (agent.knowledge_base_id || null)
              }
            >
              {updateMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  保存中…
                </>
              ) : (
                "保存"
              )}
            </Button>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
            <div className="flex items-center gap-2 text-slate-300">
              <BookOpen className="h-4 w-4" />
              <span className="font-medium">字段说明</span>
            </div>
            <p className="mt-2 text-sm text-slate-400">
              <code className="rounded bg-slate-800 px-1">knowledge_base_id</code> 绑定后，
              AgentRuntime 启动时自动加载该知识库，在对话/任务执行中根据 query 进行 RAG 检索并注入上下文。
            </p>
          </div>
        </div>
      </TableShell>
    </div>
  );
}
