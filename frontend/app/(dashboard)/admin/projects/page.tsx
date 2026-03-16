"use client";

import { useQuery } from "@tanstack/react-query";
import { Activity, BriefcaseBusiness, Search } from "lucide-react";
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
import { StatusBadge } from "@/components/shared/status-badge";
import { Input } from "@/components/ui/input";
import { listAdminProjects } from "@/lib/api-admin";

export type AdminProject = {
  id: string;
  tenant_id: string;
  key: string;
  name: string;
  description: string | null;
  status: string;
  agent_count?: number;
  task_count?: number;
  workflow_count?: number;
  created_at: string;
  updated_at: string;
};

export default function AdminProjectsPage() {
  const [keyword, setKeyword] = useState("");

  const projectsQuery = useQuery({
    queryKey: ["admin-projects"],
    queryFn: () => listAdminProjects({ limit: 200 }),
  });

  const projects = (projectsQuery.data?.items ?? []) as AdminProject[];
  const total = projectsQuery.data?.total ?? 0;

  const filtered = keyword.trim()
    ? projects.filter(
        (p) =>
          p.name?.toLowerCase().includes(keyword.toLowerCase()) ||
          p.key?.toLowerCase().includes(keyword.toLowerCase())
      )
    : projects;

  return (
    <div className="space-y-6">
      <PageHero
        eyebrow="项目管理"
        title="查看平台项目"
        description="浏览所有租户下的项目。项目包含 Agent、任务和工作流。"
      />

      <section className="grid gap-4 md:grid-cols-3">
        <MetricCard label="项目总数" value={String(total)} icon={BriefcaseBusiness} />
        <MetricCard label="活跃" value={String(projects.filter((p) => p.status === "active").length)} />
        <MetricCard label="草稿" value={String(projects.filter((p) => p.status === "draft").length)} />
      </section>

      <FilterBar title="搜索" description="按名称或 Key 搜索项目。">
        <div className="relative min-w-[260px] flex-1">
          <Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-slate-400" />
          <Input
            className="pl-9"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="搜索项目…"
          />
        </div>
      </FilterBar>

      <TableShell>
        <div className="p-6">
          <PanelHeader
            title="项目列表"
            description="平台上的所有项目。"
          />
          {projectsQuery.isLoading ? (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-12 text-center text-sm text-slate-400">
              加载中…
            </div>
          ) : filtered.length === 0 ? (
            <EmptyState
              title="暂无项目"
              description={keyword ? "没有匹配的项目。" : "暂无项目。"}
              icon={Activity}
            />
          ) : (
            <DataTable headers={["项目", "Key", "状态", "统计", "创建时间"]}>
              {filtered.map((p) => (
                <DataRow key={p.id}>
                  <DataCell>
                    <div>
                      <p className="font-medium text-slate-100">{p.name}</p>
                      <p className="text-xs text-slate-500">{p.id}</p>
                    </div>
                  </DataCell>
                  <DataCell className="font-mono text-slate-300">{p.key}</DataCell>
                  <DataCell>
                    <StatusBadge value={p.status} />
                  </DataCell>
                  <DataCell className="text-slate-400">
                    Agent: {p.agent_count ?? 0} · 任务: {p.task_count ?? 0} · 工作流: {p.workflow_count ?? 0}
                  </DataCell>
                  <DataCell className="text-slate-400">
                    {p.created_at ? new Date(p.created_at).toLocaleDateString() : "-"}
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
