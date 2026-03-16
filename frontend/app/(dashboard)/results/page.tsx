"use client";

import { useQuery } from "@tanstack/react-query";
import { ListTodo, ScrollText, TerminalSquare } from "lucide-react";
import { useEffect, useState } from "react";

import { HeroTip, PageHero } from "@/components/shared/admin-kit";
import { EmptyState } from "@/components/shared/empty-state";
import { StatusBadge } from "@/components/shared/status-badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getExecution, getTask, listExecutions, listTasks } from "@/lib/api";

type ResultsTab = "tasks" | "workflows";

function formatTimestamp(value: string | null | undefined) {
  if (!value) return "—";
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit"
  }).format(new Date(value));
}

export default function ResultsPage() {
  const [activeTab, setActiveTab] = useState<ResultsTab>("tasks");
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [selectedExecutionId, setSelectedExecutionId] = useState<string | null>(null);

  const tasksQuery = useQuery({
    queryKey: ["tasks"],
    queryFn: () => listTasks({ limit: 100 }),
    refetchInterval: 5000
  });

  const executionsQuery = useQuery({
    queryKey: ["executions"],
    queryFn: () => listExecutions().catch(() => []),
    refetchInterval: 5000
  });

  const executedTasks = (tasksQuery.data ?? []).filter(
    (t) => t.status === "completed" || t.status === "failed" || t.status === "running"
  );

  const selectedTaskDetailQuery = useQuery({
    queryKey: ["task", selectedTaskId],
    queryFn: () => getTask(selectedTaskId ?? ""),
    enabled: Boolean(selectedTaskId),
    refetchInterval: selectedTaskId ? 3000 : false
  });

  const executionDetailQuery = useQuery({
    queryKey: ["execution", selectedExecutionId],
    queryFn: () => getExecution(selectedExecutionId ?? ""),
    enabled: Boolean(selectedExecutionId),
    refetchInterval: selectedExecutionId ? 5000 : false
  });

  useEffect(() => {
    if (activeTab === "tasks" && !selectedTaskId && executedTasks[0]) {
      setSelectedTaskId(executedTasks[0].id);
    }
  }, [activeTab, selectedTaskId, executedTasks]);

  useEffect(() => {
    if (activeTab === "workflows" && !selectedExecutionId && (executionsQuery.data ?? []).length > 0) {
      setSelectedExecutionId(executionsQuery.data![0].execution_id);
    }
  }, [activeTab, selectedExecutionId, executionsQuery.data]);

  const taskDetail = selectedTaskDetailQuery.data;
  const outputPayload = taskDetail?.output_payload ?? {};

  return (
    <div className="space-y-6">
      <PageHero
        eyebrow="执行日志与结果中心"
        title="统一查看任务执行与流程运行结果"
        description="任务经由 Agent Runtime 执行后，输出会在此展示。支持任务执行结果与工作流执行记录两种视图。"
      >
        <HeroTip label="任务执行" value="创建任务 → 分配 Agent → 点击运行，结果会在此展示 output_payload。" />
        <HeroTip label="流程执行" value="由工作流引擎触发的流程，可查看步骤时间线与上下文。" />
      </PageHero>

      <div className="flex flex-col gap-6">
      <div className="flex gap-2 rounded-xl border border-slate-800 bg-slate-900/50 p-1 w-fit">
        <button
          type="button"
          onClick={() => setActiveTab("tasks")}
          className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition ${
            activeTab === "tasks"
              ? "bg-sky-500/20 text-sky-200 shadow-sm"
              : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
          }`}
        >
          <ListTodo className="h-4 w-4" />
          任务执行
          {executedTasks.length > 0 && (
            <span className="rounded-full bg-sky-500/30 px-2 py-0.5 text-xs">{executedTasks.length}</span>
          )}
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("workflows")}
          className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition ${
            activeTab === "workflows"
              ? "bg-sky-500/20 text-sky-200 shadow-sm"
              : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
          }`}
        >
          <ScrollText className="h-4 w-4" />
          流程执行
          {(executionsQuery.data ?? []).length > 0 && (
            <span className="rounded-full bg-sky-500/30 px-2 py-0.5 text-xs">
              {(executionsQuery.data ?? []).length}
            </span>
          )}
        </button>
      </div>

      <div className="min-h-[300px]">
      {activeTab === "tasks" && (
          <div className="mt-6 grid gap-6 xl:grid-cols-[340px_1fr]">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ListTodo className="h-5 w-5 text-sky-600" />
                  任务执行列表
                </CardTitle>
                <CardDescription>选择一项任务，查看 Agent Runtime 的真实输出。</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {executedTasks.length === 0 ? (
                  <EmptyState
                    title="暂无任务执行记录"
                    description="在任务页创建任务、分配 Agent 并点击运行后，执行结果会展示在这里。"
                    icon={ListTodo}
                  />
                ) : (
                  executedTasks.map((task) => (
                    <button
                      key={task.id}
                      className={`w-full rounded-2xl border p-4 text-left transition ${
                        selectedTaskId === task.id
                          ? "border-sky-500/30 bg-sky-500/10 shadow-[inset_3px_0_0_0_rgba(56,189,248,0.9)]"
                          : "border-slate-800 bg-slate-900/70 hover:bg-slate-900 active:bg-slate-800"
                      }`}
                      onClick={() => setSelectedTaskId(task.id)}
                    >
                      <div className="flex items-center justify-between gap-3">
                        <p className="truncate font-medium text-slate-100" title={task.title}>
                          {task.title}
                        </p>
                        <StatusBadge value={task.status} />
                      </div>
                      <p className="mt-1 text-xs text-slate-400">
                        {task.status === "completed" || task.status === "failed"
                          ? `${task.status === "completed" ? "完成" : "失败"} · ${formatTimestamp(task.updated_at)}`
                          : `执行中 · 尝试 ${task.attempt_count}/${task.max_attempts}`}
                      </p>
                    </button>
                  ))
                )}
              </CardContent>
            </Card>

            <div className="space-y-6">
              {selectedTaskId && taskDetail ? (
                <>
                  <Card>
                    <CardHeader>
                      <CardTitle>任务详情</CardTitle>
                      <CardDescription>任务元数据与 Agent Runtime 执行输出。</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="flex flex-wrap items-center gap-3 text-sm">
                        <StatusBadge value={taskDetail.status} />
                        <span className="text-slate-400">任务：{taskDetail.title}</span>
                        {taskDetail.completed_at && (
                          <span className="text-slate-500">完成：{formatTimestamp(taskDetail.completed_at)}</span>
                        )}
                      </div>
                      {taskDetail.last_error && (
                        <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-4">
                          <p className="text-sm font-medium text-red-300">错误信息</p>
                          <pre className="mt-2 overflow-x-auto rounded-xl bg-slate-950 p-3 text-xs text-red-200">
                            {taskDetail.last_error}
                          </pre>
                        </div>
                      )}
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <TerminalSquare className="h-5 w-5 text-sky-600" />
                        执行输出 (output_payload)
                      </CardTitle>
                      <CardDescription>Agent Runtime 返回的 result、plan_summary、logs、tool_results 等。</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {Object.keys(outputPayload).length === 0 ? (
                        <p className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 text-sm text-slate-400">
                          暂无输出（任务可能仍在执行中，或执行未产生结果载荷）
                        </p>
                      ) : (
                        <>
                          {(outputPayload.result as Record<string, unknown>)?.content && (
                            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
                              <h3 className="mb-2 font-semibold text-slate-100">Result Content</h3>
                              <pre className="overflow-x-auto rounded-xl bg-slate-950 p-4 text-xs text-slate-300 whitespace-pre-wrap">
                                {String((outputPayload.result as Record<string, unknown>).content)}
                              </pre>
                            </div>
                          )}
                          {outputPayload.plan_summary && (
                            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
                              <h3 className="mb-2 font-semibold text-slate-100">Plan Summary</h3>
                              <p className="text-sm text-slate-300">{String(outputPayload.plan_summary)}</p>
                            </div>
                          )}
                          {(outputPayload.logs as unknown[])?.length > 0 && (
                            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
                              <h3 className="mb-2 font-semibold text-slate-100">Logs</h3>
                              <pre className="overflow-x-auto rounded-xl bg-slate-950 p-4 text-xs text-slate-300">
                                {JSON.stringify(outputPayload.logs, null, 2)}
                              </pre>
                            </div>
                          )}
                          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
                            <h3 className="mb-2 font-semibold text-slate-100">完整 output_payload</h3>
                            <pre className="overflow-x-auto rounded-xl bg-slate-950 p-4 text-xs text-slate-300">
                              {JSON.stringify(outputPayload, null, 2)}
                            </pre>
                          </div>
                        </>
                      )}
                    </CardContent>
                  </Card>
                </>
              ) : (
                <Card>
                  <CardContent className="flex min-h-[200px] items-center justify-center py-12">
                    <EmptyState
                      title="请选择任务"
                      description="从左侧列表选择一项已执行的任务，查看其输出。"
                      icon={ListTodo}
                    />
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
      )}

      {activeTab === "workflows" && (
          <div className="mt-6 grid gap-6 xl:grid-cols-[340px_1fr]">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ScrollText className="h-5 w-5 text-sky-600" />
                  流程执行列表
                </CardTitle>
                <CardDescription>选择一次流程执行，查看运行状态、上下文和步骤轨迹。</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {(executionsQuery.data ?? []).length === 0 ? (
                  <EmptyState
                    title="暂无流程执行记录"
                    description="当工作流流程开始运行后，相关的执行记录会展示在这里。"
                    icon={ScrollText}
                  />
                ) : (
                  (executionsQuery.data ?? []).map((execution) => (
                    <button
                      key={execution.execution_id}
                      className={`w-full rounded-2xl border p-4 text-left transition ${
                        selectedExecutionId === execution.execution_id
                          ? "border-sky-500/30 bg-sky-500/10 shadow-[inset_3px_0_0_0_rgba(56,189,248,0.9)]"
                          : "border-slate-800 bg-slate-900/70 hover:bg-slate-900 active:bg-slate-800"
                      }`}
                      onClick={() => setSelectedExecutionId(execution.execution_id)}
                    >
                      <div className="flex items-center justify-between gap-3">
                        <p className="font-medium text-slate-100">{execution.execution_id}</p>
                        <StatusBadge value={execution.status} />
                      </div>
                      <p className="mt-1 text-xs text-slate-400">
                        {execution.current_step ? `当前步骤：${execution.current_step}` : "执行完成"}
                      </p>
                    </button>
                  ))
                )}
              </CardContent>
            </Card>

            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>执行详情</CardTitle>
                  <CardDescription>查看当前执行记录的状态摘要和上下文载荷。</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
                    <div className="flex flex-wrap items-center gap-3 text-sm">
                      <StatusBadge value={executionDetailQuery.data?.status ?? "idle"} />
                      <span className="text-slate-400">流程：{executionDetailQuery.data?.workflow_name ?? "暂无"}</span>
                    </div>
                    <pre className="mt-4 overflow-x-auto rounded-xl bg-slate-950 p-4 text-xs text-slate-300">
                      {JSON.stringify(executionDetailQuery.data?.context ?? {}, null, 2)}
                    </pre>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TerminalSquare className="h-5 w-5 text-sky-600" />
                    步骤时间线
                  </CardTitle>
                  <CardDescription>查看每个步骤的输出、流转关系和异常信息。</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {(executionDetailQuery.data?.step_history ?? []).map((step) => (
                    <div
                      key={`${step.step_key}-${step.started_at}`}
                      className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5"
                    >
                      <div className="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
                        <div>
                          <h3 className="font-semibold text-slate-100">{step.step_key}</h3>
                          <p className="text-sm text-slate-400">
                            {step.step_type} {step.next_step ? `→ ${step.next_step}` : "→ 结束"}
                          </p>
                        </div>
                        <div className="flex items-center gap-3">
                          <StatusBadge value={step.status} />
                          <p className="text-xs text-slate-500">{step.started_at}</p>
                        </div>
                      </div>
                      <pre className="mt-4 overflow-x-auto rounded-xl bg-slate-950 p-4 text-xs text-slate-300">
                        {JSON.stringify(step.output, null, 2)}
                      </pre>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>
          </div>
      )}
      </div>
      </div>
    </div>
  );
}
