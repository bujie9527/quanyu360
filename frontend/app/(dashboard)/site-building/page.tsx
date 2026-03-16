"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronDown, ChevronUp, Globe, Loader2, Plus, Wrench } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import {
  createSiteBuildingBatch,
  getTenantQuotas,
  getTaskRun,
  listSitePlans,
  listPlatformDomainsAvailable,
  listProjects,
  listTaskRuns,
  listWorkflows,
} from "@/lib/api";

export default function SiteBuildingPage() {
  const queryClient = useQueryClient();
  const [projectId, setProjectId] = useState<string>("");
  const [workflowId, setWorkflowId] = useState<string>("");
  const [sitePlanId, setSitePlanId] = useState<string>("");
  const [count, setCount] = useState(1);
  const [domainIds, setDomainIds] = useState<string[]>([]);

  const projectsQuery = useQuery({
    queryKey: ["projects"],
    queryFn: () => listProjects(),
  });

  const domainsQuery = useQuery({
    queryKey: ["platform-domains-available"],
    queryFn: () => listPlatformDomainsAvailable(),
  });

  const quotasQuery = useQuery({
    queryKey: ["quotas"],
    queryFn: () => getTenantQuotas(),
  });

  const workflowsQuery = useQuery({
    queryKey: ["workflows", projectId],
    queryFn: () => listWorkflows({ project_id: projectId }),
    enabled: !!projectId,
  });
  const sitePlansQuery = useQuery({
    queryKey: ["site-plans", projectId, "approved"],
    queryFn: () => listSitePlans(projectId, { status: "approved", limit: 50 }),
    enabled: !!projectId,
  });

  const taskRunsQuery = useQuery({
    queryKey: ["task-runs", projectId],
    queryFn: () => listTaskRuns({ project_id: projectId, limit: 50 }),
    enabled: !!projectId,
    refetchInterval: 3000,
  });

  useEffect(() => {
    if (!projectId && projectsQuery.data?.[0]?.id) {
      setProjectId(projectsQuery.data[0].id);
    }
  }, [projectsQuery.data, projectId]);

  useEffect(() => {
    const activeWorkflows = (workflowsQuery.data ?? []).filter((wf) => wf.status === "active");
    if (activeWorkflows.length === 0) {
      setWorkflowId("");
      return;
    }
    if (!activeWorkflows.some((wf) => wf.id === workflowId)) {
      setWorkflowId(activeWorkflows[0].id);
    }
  }, [workflowId, workflowsQuery.data]);

  useEffect(() => {
    if (!sitePlanId) return;
    const selectedPlan = (sitePlansQuery.data?.items ?? []).find((p) => p.id === sitePlanId);
    if (!selectedPlan) return;
    const plannedCount = Math.max(1, selectedPlan.items.length || 1);
    setCount(plannedCount);
    setDomainIds((domainsQuery.data ?? []).slice(0, plannedCount).map((d) => d.id));
  }, [sitePlanId, sitePlansQuery.data, domainsQuery.data]);

  const createMutation = useMutation({
    mutationFn: createSiteBuildingBatch,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["task-runs"] });
      queryClient.invalidateQueries({ queryKey: ["quotas"] });
      queryClient.invalidateQueries({ queryKey: ["platform-domains-available"] });
      setDomainIds([]);
    },
  });

  const wpQuota = useMemo(() => {
    const q = quotasQuery.data?.quotas?.wordpress_sites_per_month;
    if (!q) return { current: 0, limit: 0, allowed: true };
    return q;
  }, [quotasQuery.data]);

  const remaining = Math.max(0, wpQuota.limit - wpQuota.current);

  const canSubmit =
    projectId &&
    workflowId &&
    count >= 1 &&
    count <= remaining &&
    domainIds.length >= count &&
    !createMutation.isPending;

  const toggleDomain = (id: string) => {
    setDomainIds((prev) =>
      prev.includes(id) ? prev.filter((d) => d !== id) : [...prev, id]
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm text-slate-400">WordPress 自动建站</p>
        <h1 className="text-2xl font-semibold text-slate-100">建站任务</h1>
        <p className="mt-1 text-slate-400">
          选择项目与可用域名，批量创建 WordPress 建站任务
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Plus className="h-5 w-5" />
              创建建站任务
            </CardTitle>
            <CardDescription>
              选择项目、数量及可用域名，创建批量建站任务。每月配额：{wpQuota.current}/{wpQuota.limit}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>项目</Label>
              <select
                className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
                value={projectId}
                onChange={(e) => setProjectId(e.target.value)}
              >
                <option value="">选择项目</option>
                {(projectsQuery.data ?? []).map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.key})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <Label>使用站点规划方案（可选）</Label>
              <select
                className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
                value={sitePlanId}
                onChange={(e) => setSitePlanId(e.target.value)}
                disabled={!projectId}
              >
                <option value="">手动配置</option>
                {(sitePlansQuery.data?.items ?? []).map((plan) => (
                  <option key={plan.id} value={plan.id}>
                    {plan.status} · {plan.items.length} 个站点
                  </option>
                ))}
              </select>
            </div>

            <div>
              <Label>建站数量 (剩余配额: {remaining})</Label>
              <input
                type="number"
                min={1}
                max={remaining}
                value={count}
                onChange={(e) => setCount(Math.max(1, parseInt(e.target.value, 10) || 1))}
                className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
              />
              {count > remaining && (
                <p className="mt-1 text-sm text-amber-500">超出剩余配额</p>
              )}
            </div>

            <div>
              <Label>执行工作流</Label>
              <select
                className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
                value={workflowId}
                onChange={(e) => setWorkflowId(e.target.value)}
                disabled={!projectId}
              >
                <option value="">选择工作流</option>
                {(workflowsQuery.data ?? [])
                  .filter((wf) => wf.status === "active")
                  .map((wf) => (
                    <option key={wf.id} value={wf.id}>
                      {wf.name}
                    </option>
                  ))}
              </select>
              {projectId && (workflowsQuery.data ?? []).filter((wf) => wf.status === "active").length === 0 && (
                <p className="mt-1 text-sm text-amber-500">当前项目没有可执行的 active workflow，请先发布一个工作流。</p>
              )}
            </div>

            <div>
              <Label>选择域名 (至少选 {count} 个)</Label>
              <div className="mt-2 max-h-48 space-y-2 overflow-y-auto rounded-lg border border-slate-700 p-2">
                {(domainsQuery.data ?? []).map((d) => (
                  <label
                    key={d.id}
                    className="flex cursor-pointer items-center gap-2 rounded px-2 py-1.5 hover:bg-slate-800"
                  >
                    <input
                      type="checkbox"
                      checked={domainIds.includes(d.id)}
                      onChange={() => toggleDomain(d.id)}
                    />
                    <Globe className="h-4 w-4 text-slate-500" />
                    <span className="text-sm text-slate-200">{d.domain}</span>
                  </label>
                ))}
                {domainsQuery.data?.length === 0 && (
                  <p className="py-4 text-center text-sm text-slate-500">暂无可用域名</p>
                )}
              </div>
            </div>

            <Button
              className="w-full"
              disabled={!canSubmit}
              onClick={() =>
                createMutation.mutate({
                  project_id: projectId,
                  count,
                  domain_ids: domainIds.slice(0, count),
                  workflow_id: workflowId || null,
                })
              }
            >
              {createMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  创建中...
                </>
              ) : (
                "创建建站任务"
              )}
            </Button>
            {createMutation.isError && (
              <p className="text-sm text-red-500">{String(createMutation.error)}</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>任务执行列表</CardTitle>
            <CardDescription>
              任务每 3 秒自动刷新，展示执行进度
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {(taskRunsQuery.data?.items ?? []).map((tr) => (
                <TaskRunRow key={tr.id} taskRunId={tr.id} />
              ))}
              {(taskRunsQuery.data?.items ?? []).length === 0 && (
                <p className="py-8 text-center text-slate-500">暂无建站任务</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function TaskRunRow({ taskRunId }: { taskRunId: string }) {
  const [expanded, setExpanded] = useState(false);
  const { data, isLoading } = useQuery({
    queryKey: ["task-run", taskRunId],
    queryFn: () => getTaskRun(taskRunId),
    refetchInterval: 3000,
  });

  if (isLoading || !data) {
    return (
      <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-3">
        <Loader2 className="h-4 w-4 animate-spin text-slate-500" />
      </div>
    );
  }

  const steps = data.step_runs ?? [];
  const domainHint =
    (steps
      .map((s) => s.output_json?.domain)
      .find((v): v is string => typeof v === "string" && v.trim().length > 0)
      ?.trim()) ?? "";
  const themeHint =
    (steps
      .map((s) => s.output_json?.site_theme)
      .find((v): v is string => typeof v === "string" && v.trim().length > 0)
      ?.trim()) ?? "";
  const currentStepIndex = steps.findIndex((s) => s.status === "running" || s.status === "pending");
  const currentStep = currentStepIndex >= 0 ? steps[currentStepIndex] : null;
  const progressLabel =
    steps.length > 0
      ? currentStep
        ? `步骤 ${currentStepIndex + 1}/${steps.length} · 正在执行: ${currentStep.step_name}`
        : `步骤 ${steps.length}/${steps.length} · 已完成`
      : data.status === "running"
        ? "等待步骤..."
        : "";

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-3">
      <button
        type="button"
        className="flex w-full items-center justify-between text-left"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex flex-col items-start gap-1">
          <span className="text-sm font-medium text-slate-200">
            {domainHint || `${data.execution_id.slice(0, 8)}...`}
          </span>
          {themeHint ? <span className="text-xs text-slate-500">{themeHint}</span> : null}
          {progressLabel && (
            <span className="text-xs text-slate-400">{progressLabel}</span>
          )}
        </div>
        <span className="flex items-center gap-2">
          <span
            className={`rounded px-2 py-0.5 text-xs ${
              data.status === "completed"
                ? "bg-emerald-500/20 text-emerald-400"
                : data.status === "failed"
                  ? "bg-red-500/20 text-red-400"
                  : "bg-amber-500/20 text-amber-400"
            }`}
          >
            {data.status}
          </span>
          {expanded ? (
            <ChevronUp className="h-4 w-4 text-slate-500" />
          ) : (
            <ChevronDown className="h-4 w-4 text-slate-500" />
          )}
        </span>
      </button>
      <div className="mt-2 space-y-1">
        {steps.map((sr, idx) => (
          <div
            key={sr.id}
            className={`flex items-center gap-2 text-xs ${
              sr.status === "running" ? "text-amber-400" : "text-slate-400"
            }`}
          >
            <span className="w-6 text-slate-500">{idx + 1}.</span>
            <span className="w-28 truncate">{sr.step_name}</span>
            <span className="rounded bg-slate-800 px-1.5 py-0.5">{sr.status}</span>
            <span>{sr.duration > 0 ? `${sr.duration.toFixed(2)}s` : ""}</span>
          </div>
        ))}
      </div>
      {expanded && (
        <div className="mt-3 space-y-3 border-t border-slate-800 pt-3">
          {steps
            .map((sr) => {
              const out = sr.output_json ?? {};
              const hasContent =
                (Array.isArray(out.logs) && out.logs.length > 0) ||
                (Array.isArray(out.tool_results) && out.tool_results.length > 0) ||
                out.content ||
                out.error_message ||
                (out.result && typeof out.result === "object" && Object.keys(out.result).length > 0);
              if (!hasContent) return null;
            return (
              <div
                key={sr.id}
                className="rounded-lg border border-slate-700 bg-slate-900/80 p-3"
              >
                <p className="mb-2 text-xs font-medium text-slate-300">
                  {sr.step_name} · 输出
                </p>
                {out.error_message != null && String(out.error_message).trim() !== "" ? (
                  <div className="mb-2 rounded border border-red-500/30 bg-red-500/10 p-2 text-xs text-red-300">
                    {String(out.error_message)}
                  </div>
                ) : null}
                {(out.logs as unknown[])?.length > 0 && (
                  <div className="mb-2">
                    <p className="mb-1 text-xs text-slate-500">日志</p>
                    <pre className="max-h-32 overflow-auto rounded bg-slate-950 p-2 text-xs text-slate-400">
                      {JSON.stringify(out.logs, null, 2)}
                    </pre>
                  </div>
                )}
                {(out.tool_results as unknown[])?.length > 0 && (
                  <div className="mb-2">
                    <p className="mb-1 flex items-center gap-1 text-xs text-slate-500">
                      <Wrench className="h-3 w-3" /> 工具调用
                    </p>
                    <pre className="max-h-40 overflow-auto rounded bg-slate-950 p-2 text-xs text-slate-400">
                      {JSON.stringify(out.tool_results, null, 2)}
                    </pre>
                  </div>
                )}
                {out.content != null && String(out.content).trim() !== "" ? (
                  <div className="mb-2">
                    <p className="mb-1 text-xs text-slate-500">内容</p>
                    <pre className="max-h-32 overflow-auto rounded bg-slate-950 p-2 text-xs text-slate-300 whitespace-pre-wrap">
                      {String(out.content)}
                    </pre>
                  </div>
                ) : null}
                {out.result != null && typeof out.result === "object" && out.content == null ? (
                  <pre className="max-h-32 overflow-auto rounded bg-slate-950 p-2 text-xs text-slate-400">
                    {JSON.stringify(out.result, null, 2)}
                  </pre>
                ) : null}
              </div>
            );
          })}
          {steps.length > 0 &&
            !steps.some((sr) => {
              const o = sr.output_json ?? {};
              return (
                (Array.isArray(o.logs) && o.logs.length > 0) ||
                (Array.isArray(o.tool_results) && o.tool_results.length > 0) ||
                o.content ||
                o.error_message ||
                (o.result && typeof o.result === "object" && Object.keys(o.result).length > 0)
              );
            }) && (
              <p className="py-2 text-xs text-slate-500">
                暂无步骤输出详情（执行中或步骤尚未写入日志/工具结果）
              </p>
            )}
        </div>
      )}
    </div>
  );
}
