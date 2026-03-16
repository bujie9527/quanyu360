"use client";

import { useQuery } from "@tanstack/react-query";
import { GitBranchPlus, Search } from "lucide-react";
import { useState } from "react";

import {
  DataCell,
  DataRow,
  DataTable,
  FilterBar,
  MetricCard,
  PageHero,
  PanelHeader,
  TableShell
} from "@/components/shared/admin-kit";
import { EmptyState } from "@/components/shared/empty-state";
import { StatusBadge } from "@/components/shared/status-badge";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from "@/components/ui/select";
import { listAdminProjects, listAdminWorkflows } from "@/lib/api-admin";

export type AdminWorkflow = {
  id: string;
  project_id: string;
  name: string;
  slug: string;
  version: number;
  status: string;
  trigger_type: string;
  step_count?: number;
  created_at: string;
  updated_at: string;
};

export default function AdminWorkflowsPage() {
  const [projectFilter, setProjectFilter] = useState<string>("");
  const [keyword, setKeyword] = useState("");

  const projectsQuery = useQuery({
    queryKey: ["admin-projects"],
    queryFn: () => listAdminProjects({ limit: 500 })
  });

  const workflowsQuery = useQuery({
    queryKey: ["admin-workflows", projectFilter],
    queryFn: () =>
      listAdminWorkflows({
        project_id: projectFilter || undefined,
        limit: 200
      })
  });

  const workflows = (workflowsQuery.data?.items ?? []) as AdminWorkflow[];
  const total = workflowsQuery.data?.total ?? 0;
  const projects = (projectsQuery.data?.items ?? []) as { id: string; name?: string; key?: string }[];

  const filtered =
    keyword.trim()
      ? workflows.filter(
          (w) =>
            w.name?.toLowerCase().includes(keyword.toLowerCase()) ||
            w.slug?.toLowerCase().includes(keyword.toLowerCase()) ||
            w.id?.toLowerCase().includes(keyword.toLowerCase())
        )
      : workflows;

  const statusCounts = {
    draft: workflows.filter((w) => w.status === "draft").length,
    active: workflows.filter((w) => w.status === "active").length,
    archived: workflows.filter((w) => w.status === "archived").length
  };

  return (
    <div className="space-y-6">
      <PageHero
        eyebrow="流程管理"
        title="查看平台工作流"
        description="跨项目查看所有工作流，监控配置与发布状态。"
      />

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard label="工作流总数" value={String(total)} icon={GitBranchPlus} />
        <MetricCard label="草稿" value={String(statusCounts.draft)} />
        <MetricCard label="已发布" value={String(statusCounts.active)} />
        <MetricCard label="已归档" value={String(statusCounts.archived)} />
      </section>

      <FilterBar title="筛选" description="按项目筛选，按名称或 slug 搜索。">
        <Select value={projectFilter} onValueChange={setProjectFilter}>
          <SelectTrigger className="max-w-[220px]">
            <SelectValue placeholder="全部项目" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">全部项目</SelectItem>
            {projects.map((p) => (
              <SelectItem key={p.id} value={p.id}>
                {p.name ?? p.key ?? p.id}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <div className="relative min-w-[260px] flex-1">
          <Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-slate-400" />
          <Input
            className="pl-9"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="搜索工作流名称或 slug…"
          />
        </div>
      </FilterBar>

      <TableShell>
        <div className="p-6">
          <PanelHeader
            title="工作流列表"
            description="平台上的所有工作流。"
          />
          {filtered.length === 0 ? (
            <EmptyState
              title="暂无工作流"
              description={keyword || projectFilter ? "没有匹配的工作流。" : "暂无工作流数据。"}
              icon={GitBranchPlus}
            />
          ) : (
            <DataTable
              headers={["名称", "标识", "版本", "状态", "触发方式", "步骤数", "项目", "创建时间"]}
            >
              {filtered.map((w) => {
                const project = projects.find((p) => p.id === w.project_id);
                return (
                  <DataRow key={w.id}>
                    <DataCell>
                      <div>
                        <p className="font-medium text-slate-100">{w.name}</p>
                        <p className="text-xs text-slate-500">{w.id}</p>
                      </div>
                    </DataCell>
                    <DataCell className="font-mono text-slate-300">{w.slug}</DataCell>
                    <DataCell className="text-slate-400">v{w.version}</DataCell>
                    <DataCell>
                      <StatusBadge value={w.status} />
                    </DataCell>
                    <DataCell className="text-slate-400">{w.trigger_type ?? "manual"}</DataCell>
                    <DataCell className="text-slate-400">{w.step_count ?? "—"}</DataCell>
                    <DataCell className="text-slate-400">
                      {project?.name ?? project?.key ?? w.project_id?.slice(0, 8)}
                    </DataCell>
                    <DataCell className="text-slate-400">
                      {w.created_at ? new Date(w.created_at).toLocaleDateString() : "-"}
                    </DataCell>
                  </DataRow>
                );
              })}
            </DataTable>
          )}
        </div>
      </TableShell>
    </div>
  );
}
