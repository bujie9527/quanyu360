"use client";

import { useQuery } from "@tanstack/react-query";
import { ListTodo, Search } from "lucide-react";
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
import { listAdminTasks } from "@/lib/api-admin";

export type AdminTask = {
  id: string;
  title: string;
  description: string | null;
  status: string;
  priority: string;
  project_id: string;
  agent_id: string | null;
  workflow_id: string | null;
  attempt_count?: number;
  max_attempts?: number;
  created_at: string;
  updated_at: string;
};

export default function AdminTasksPage() {
  const [keyword, setKeyword] = useState("");

  const tasksQuery = useQuery({
    queryKey: ["admin-tasks"],
    queryFn: () => listAdminTasks({ limit: 200 })
  });

  const tasks = (tasksQuery.data?.items ?? []) as AdminTask[];
  const total = tasksQuery.data?.total ?? 0;

  const filtered = keyword.trim()
    ? tasks.filter(
        (t) =>
          t.title?.toLowerCase().includes(keyword.toLowerCase()) ||
          t.id?.toLowerCase().includes(keyword.toLowerCase())
      )
    : tasks;

  const statusCounts = {
    pending: tasks.filter((t) => t.status === "pending").length,
    running: tasks.filter((t) => t.status === "running").length,
    completed: tasks.filter((t) => t.status === "completed").length,
    failed: tasks.filter((t) => t.status === "failed").length
  };

  return (
    <div className="space-y-6">
      <PageHero
        eyebrow="任务管理"
        title="查看平台任务"
        description="跨项目查看所有任务，监控执行状态与队列情况。"
      />

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <MetricCard label="任务总数" value={String(total)} icon={ListTodo} />
        <MetricCard label="待处理" value={String(statusCounts.pending)} />
        <MetricCard label="运行中" value={String(statusCounts.running)} />
        <MetricCard label="已完成" value={String(statusCounts.completed)} />
        <MetricCard label="失败" value={String(statusCounts.failed)} />
      </section>

      <FilterBar title="搜索" description="按标题或 ID 搜索任务。">
        <div className="relative min-w-[260px] flex-1">
          <Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-slate-400" />
          <Input
            className="pl-9"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="搜索任务…"
          />
        </div>
      </FilterBar>

      <TableShell>
        <div className="p-6">
          <PanelHeader
            title="任务列表"
            description="平台上的所有任务。"
          />
          {tasksQuery.isLoading ? (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-12 text-center text-sm text-slate-400">
              加载中…
            </div>
          ) : filtered.length === 0 ? (
            <EmptyState
              title="暂无任务"
              description={keyword ? "没有匹配的任务。" : "暂无任务。"}
              icon={ListTodo}
            />
          ) : (
            <DataTable headers={["任务", "状态", "优先级", "项目 ID", "Agent ID", "创建时间"]}>
              {filtered.map((t) => (
                <DataRow key={t.id}>
                  <DataCell>
                    <div>
                      <p className="font-medium text-slate-100">{t.title}</p>
                      <p className="max-w-xs truncate text-xs text-slate-500">
                        {t.description || t.id}
                      </p>
                    </div>
                  </DataCell>
                  <DataCell>
                    <StatusBadge value={t.status} />
                  </DataCell>
                  <DataCell className="text-slate-300">{t.priority ?? "-"}</DataCell>
                  <DataCell className="max-w-[100px] truncate font-mono text-xs text-slate-400">
                    {t.project_id?.slice(0, 8) ?? "-"}
                  </DataCell>
                  <DataCell className="max-w-[100px] truncate font-mono text-xs text-slate-400">
                    {t.agent_id?.slice(0, 8) ?? "-"}
                  </DataCell>
                  <DataCell className="text-slate-400">
                    {t.created_at ? new Date(t.created_at).toLocaleDateString() : "-"}
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
