"use client";

import { useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getTaskRun, listProjects, listSitePlans, listTaskRuns, listWordPressSites, type TaskRunItem } from "@/lib/api";

export default function MatrixSitesPage() {
  const [projectId, setProjectId] = useState("");
  const [selectedSiteId, setSelectedSiteId] = useState<string>("");

  const projectsQuery = useQuery({ queryKey: ["projects"], queryFn: () => listProjects() });
  const matrixProjects = useMemo(() => (projectsQuery.data ?? []).filter((p) => p.project_type === "matrix_site"), [projectsQuery.data]);

  useEffect(() => {
    if (!projectId && matrixProjects[0]?.id) setProjectId(matrixProjects[0].id);
  }, [matrixProjects, projectId]);

  const sitesQuery = useQuery({
    queryKey: ["wordpress-sites", projectId],
    queryFn: () => listWordPressSites(projectId),
    enabled: !!projectId,
  });
  const plansQuery = useQuery({
    queryKey: ["site-plans", projectId, "approved"],
    queryFn: () => listSitePlans(projectId, { status: "approved", limit: 50 }),
    enabled: !!projectId,
  });
  const taskRunsQuery = useQuery({
    queryKey: ["task-runs", projectId],
    queryFn: () => listTaskRuns({ project_id: projectId, limit: 100 }),
    enabled: !!projectId,
    refetchInterval: 5000,
  });

  const allPlanItems = useMemo(
    () => (plansQuery.data?.items ?? []).flatMap((plan) => plan.items),
    [plansQuery.data]
  );
  const sites = sitesQuery.data ?? [];
  const selectedSite = sites.find((s) => s.id === selectedSiteId) ?? null;
  const selectedPlanItem =
    allPlanItems.find((item) => item.wordpress_site_id === selectedSiteId) ?? null;

  const runningCount = (taskRunsQuery.data?.items ?? []).filter((t) => t.status === "running").length;
  const activeCount = sites.filter((s) => s.status === "active").length;

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm text-slate-400">矩阵建站 / 站点管理</p>
        <h1 className="text-2xl font-semibold text-slate-100">矩阵站总览</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>项目与概览</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <select
            className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
          >
            <option value="">选择矩阵项目</option>
            {matrixProjects.map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
          <div className="grid gap-3 md:grid-cols-3">
            <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-3 text-sm text-slate-300">站点总数：{sites.length}</div>
            <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-3 text-sm text-slate-300">已激活：{activeCount}</div>
            <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-3 text-sm text-slate-300">执行中任务：{runningCount}</div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 xl:grid-cols-[1fr_360px]">
        <Card>
          <CardHeader>
            <CardTitle>站点卡片</CardTitle>
            <CardDescription>点击站点查看规划映射与执行详情</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-2">
            {sites.map((site) => {
              const planItem = allPlanItems.find((item) => item.wordpress_site_id === site.id);
              return (
                <button
                  key={site.id}
                  type="button"
                  onClick={() => setSelectedSiteId(site.id)}
                  className={`rounded-lg border p-3 text-left ${
                    selectedSiteId === site.id ? "border-sky-500 bg-sky-500/10" : "border-slate-800 bg-slate-900/50"
                  }`}
                >
                  <p className="text-sm font-medium text-slate-100">{site.domain}</p>
                  <p className="mt-1 text-xs text-slate-400">{planItem?.site_theme ?? "未绑定规划主题"}</p>
                  <p className="mt-1 text-xs text-slate-300">状态：{site.status}</p>
                </button>
              );
            })}
            {sites.length === 0 && <p className="text-sm text-slate-500">暂无站点</p>}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>站点详情</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {!selectedSite ? (
              <p className="text-sm text-slate-500">请选择左侧站点</p>
            ) : (
              <>
                <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-3">
                  <p className="text-sm font-medium text-slate-100">{selectedSite.domain}</p>
                  <p className="text-xs text-slate-400">API: {selectedSite.api_url}</p>
                  <p className="text-xs text-slate-400">状态: {selectedSite.status}</p>
                </div>
                <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-3">
                  <p className="mb-1 text-xs text-slate-400">规划信息</p>
                  {selectedPlanItem ? (
                    <>
                      <p className="text-sm text-slate-100">{selectedPlanItem.site_theme}</p>
                      <p className="text-xs text-slate-300">{selectedPlanItem.target_audience}</p>
                    </>
                  ) : (
                    <p className="text-sm text-slate-500">未匹配到 SitePlanItem</p>
                  )}
                </div>
                <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-3">
                  <p className="mb-1 text-xs text-slate-400">TaskRun 历史</p>
                  <SiteTaskRuns recentRuns={(taskRunsQuery.data?.items ?? []).slice(0, 5)} />
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function SiteTaskRuns({ recentRuns }: { recentRuns: TaskRunItem[] }) {
  if (recentRuns.length === 0) {
    return <p className="text-xs text-slate-500">暂无记录</p>;
  }
  return (
    <div className="space-y-2">
      {recentRuns.map((tr) => (
        <TaskRunSnippet key={tr.id} taskRunId={tr.id} />
      ))}
    </div>
  );
}

function TaskRunSnippet({ taskRunId }: { taskRunId: string }) {
  const query = useQuery({
    queryKey: ["task-run-snippet", taskRunId],
    queryFn: () => getTaskRun(taskRunId),
    staleTime: 10_000,
  });

  if (!query.data) return null;
  return (
    <div className="rounded border border-slate-700 p-2 text-xs text-slate-300">
      <p>{query.data.execution_id.slice(0, 8)}... · {query.data.status}</p>
      <p>步骤数：{query.data.step_runs.length}</p>
    </div>
  );
}
