"use client";

import { useQuery } from "@tanstack/react-query";
import { Bot, Search } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import {
  DataCell,
  DataRow,
  DataTable,
  FilterBar,
  MetricCard,
  PageHero,
  PanelHeader,
  TableShell,
} from "@/components/shared/admin-kit";
import { EmptyState } from "@/components/shared/empty-state";
import { Input } from "@/components/ui/input";
import { listAgentInstances, type AgentInstanceItem } from "@/lib/api-admin";

export default function AdminAgentsPage() {
  const [keyword, setKeyword] = useState("");

  const agentsQuery = useQuery({
    queryKey: ["admin-agent-instances"],
    queryFn: () => listAgentInstances({ limit: 200 }),
  });

  const agents = (agentsQuery.data?.items ?? []) as AgentInstanceItem[];
  const total = agentsQuery.data?.total ?? 0;

  const filtered = keyword.trim()
    ? agents.filter(
        (a) =>
          a.name?.toLowerCase().includes(keyword.toLowerCase()) ||
          a.template_name?.toLowerCase().includes(keyword.toLowerCase()) ||
          a.project_name?.toLowerCase().includes(keyword.toLowerCase()) ||
          a.model?.toLowerCase().includes(keyword.toLowerCase()) ||
          a.knowledge_base_name?.toLowerCase().includes(keyword.toLowerCase())
      )
    : agents;

  return (
    <div className="space-y-6">
      <PageHero
        eyebrow="AI员工"
        title="Agents"
        description="平台所有 Agent 实例，包含模板、项目、模型与知识库关联。"
      />

      <section className="grid gap-4 md:grid-cols-2">
        <MetricCard label="Agent 总数" value={String(total)} icon={Bot} />
        <MetricCard label="已启用" value={String(agents.filter((a) => (a as { enabled?: boolean }).enabled !== false).length)} />
      </section>

      <FilterBar title="搜索" description="按名称、模板、项目、模型或知识库搜索。">
        <div className="relative min-w-[260px] flex-1">
          <Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-slate-400" />
          <Input
            className="pl-9"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="搜索 Agent…"
          />
        </div>
      </FilterBar>

      <TableShell>
        <div className="p-6">
          <PanelHeader
            title="Agent 列表"
            description="name · template · project · model · knowledge_base · created_at"
          />
          {agentsQuery.isLoading ? (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-12 text-center text-sm text-slate-400">
              加载中…
            </div>
          ) : filtered.length === 0 ? (
            <EmptyState
              title="暂无 Agent"
              description={keyword ? "没有匹配的 Agent。" : "暂无 Agent 实例。"}
              icon={Bot}
            />
          ) : (
            <DataTable headers={["名称", "模板", "项目", "模型", "知识库", "创建时间"]}>
              {filtered.map((a) => (
                <DataRow key={a.id}>
                  <DataCell>
                    <Link
                      href={`/admin/agents/${a.id}`}
                      className="font-medium text-slate-100 hover:text-sky-300 hover:underline"
                    >
                      {a.name}
                    </Link>
                  </DataCell>
                  <DataCell className="text-slate-300">{a.template_name ?? "-"}</DataCell>
                  <DataCell className="text-slate-300">{a.project_name ?? "-"}</DataCell>
                  <DataCell className="font-mono text-slate-400">{a.model ?? "-"}</DataCell>
                  <DataCell className="text-slate-400">{a.knowledge_base_name ?? "-"}</DataCell>
                  <DataCell className="text-slate-400">
                    {a.created_at ? new Date(a.created_at).toLocaleString() : "-"}
                  </DataCell>
                </DataRow>
              ))}
            </DataTable>
          )}
        </div>
      </TableShell>
    </div>
  );
}
