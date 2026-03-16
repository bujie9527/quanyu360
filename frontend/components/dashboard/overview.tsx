"use client";

import { useQueries, useQuery } from "@tanstack/react-query";
import { Activity, Bot, Sigma, TimerReset } from "lucide-react";

import { AnalyticsCharts } from "@/components/dashboard/analytics-charts";
import { QuickActions } from "@/components/dashboard/quick-actions";
import { RecentExecutions } from "@/components/dashboard/recent-executions";
import { MetricCard } from "@/components/shared/metric-card";
import { PageHeader } from "@/components/shared/page-header";
import { StatusBadge } from "@/components/shared/status-badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  getRuntimeAnalytics,
  getServiceHealth,
  getTaskAnalytics,
  listAgents,
  platformServices
} from "@/lib/api";

export function Overview() {
  const agentsQuery = useQuery({
    queryKey: ["agents"],
    queryFn: () => listAgents()
  });
  const taskAnalyticsQuery = useQuery({
    queryKey: ["task-analytics"],
    queryFn: getTaskAnalytics
  });
  const runtimeAnalyticsQuery = useQuery({
    queryKey: ["runtime-analytics"],
    queryFn: getRuntimeAnalytics
  });
  const healthQueries = useQueries({
    queries: platformServices.map((service) => ({
      queryKey: ["service-health", service.name],
      queryFn: () => getServiceHealth(service)
    }))
  });

  const healthEntries = platformServices.map((service, index) => ({
    ...service,
    health: healthQueries[index]?.data ?? null
  }));

  const metrics = [
    {
      title: "累计执行任务",
      value: String(taskAnalyticsQuery.data?.tasks_executed ?? 0),
      hint: `其中已完成 ${taskAnalyticsQuery.data?.completed_tasks ?? 0} 个`,
      icon: Activity
    },
    {
      title: "Agent 成功率",
      value: `${((taskAnalyticsQuery.data?.agent_success_rate ?? 0) * 100).toFixed(1)}%`,
      hint: `当前已接入 ${agentsQuery.data?.length ?? 0} 个智能员工`,
      icon: Bot
    },
    {
      title: "平均执行时长",
      value: `${(taskAnalyticsQuery.data?.average_execution_time_seconds ?? 0).toFixed(1)}s`,
      hint: `P95 ${(taskAnalyticsQuery.data?.p95_execution_time_seconds ?? 0).toFixed(1)}s`,
      icon: TimerReset
    },
    {
      title: "Token 消耗",
      value: `${((runtimeAnalyticsQuery.data?.total_tokens_total ?? 0) / 1000).toFixed(1)}k`,
      hint: `单次平均 ${(runtimeAnalyticsQuery.data?.average_tokens_per_run ?? 0).toFixed(0)} tokens`,
      icon: Sigma
    }
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="企业运营驾驶舱"
        title="全宇企业智能营销系统"
        description="围绕项目交付、智能员工、流程编排和执行结果构建的一体化企业运营后台，信息结构对齐国内企业 SaaS 常见的总览页习惯。"
      >
        <div className="rounded-2xl border border-slate-700 bg-slate-900/80 px-4 py-3">
          <p className="text-xs text-slate-500">核心目标</p>
          <p className="mt-2 text-sm font-medium text-slate-100">提升任务交付稳定性与执行透明度</p>
        </div>
        <div className="rounded-2xl border border-slate-700 bg-slate-900/80 px-4 py-3">
          <p className="text-xs text-slate-500">推荐动作</p>
          <p className="mt-2 text-sm font-medium text-slate-100">优先配置项目、智能员工、任务模板和标准流程</p>
        </div>
      </PageHeader>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => (
          <MetricCard key={metric.title} title={metric.title} value={metric.value} description={metric.hint} icon={metric.icon} />
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.35fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>服务拓扑</CardTitle>
            <CardDescription>统一查看各个 API、执行组件与运行时服务的健康状态。</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {healthEntries.map((service) => (
              <div
                key={service.name}
                className="flex flex-col gap-3 rounded-2xl border border-slate-800 bg-slate-900/70 p-4 sm:flex-row sm:items-center sm:justify-between"
              >
                <div>
                  <p className="font-medium text-slate-100">{service.name}</p>
                  <p className="text-sm text-slate-400">{service.domain}</p>
                </div>
                <div className="flex items-center gap-3">
                  <code className="rounded-lg bg-slate-950 px-2 py-1 text-xs text-slate-300">{service.url}</code>
                  <StatusBadge value={service.health?.status ?? "unreachable"} />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>今日运营重点</CardTitle>
            <CardDescription>贴合国内 SaaS 管理台习惯的每日关注项与风险提示。</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {[
              "为每个业务项目明确负责人、交付目标和参与成员，避免资源归属不清。",
              "关键业务链路至少绑定一个标准流程模板，降低人工分发与重复配置成本。",
              "持续关注待处理任务与失败重试数，避免任务积压影响 SLA。",
              "大批量派发前先确认 Runtime、工作流引擎和依赖服务都处于健康状态。",
              "通过执行日志排查步骤跳转、工具调用结果和上下文输出是否符合预期。"
            ].map((item) => (
              <div key={item} className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 text-sm text-slate-300">
                {item}
              </div>
            ))}
            <div className="rounded-2xl border border-sky-500/20 bg-sky-500/10 p-4">
              <p className="text-sm font-medium text-sky-200">平台说明</p>
              <p className="mt-2 text-sm text-sky-100/80">
                当前监控层已接入 Prometheus 指标，前端通过 React Query 进行低打扰刷新，方便运营团队在不中断操作的前提下持续观察趋势变化。
              </p>
            </div>
          </CardContent>
        </Card>
      </section>

      <AnalyticsCharts />
      <QuickActions />
      <RecentExecutions />
    </div>
  );
}
