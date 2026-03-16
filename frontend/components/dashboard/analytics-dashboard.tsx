"use client";

import { useQueries, useQuery } from "@tanstack/react-query";
import {
  ArcElement,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
} from "chart.js";
import {
  BarChart3,
  Cpu,
  PieChart,
  Server,
  Sigma,
  TrendingUp,
} from "lucide-react";
import { Bar, Doughnut, Line } from "react-chartjs-2";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge } from "@/components/shared/status-badge";
import {
  getRuntimeAnalytics,
  getServiceHealth,
  getTaskAnalytics,
  platformServices,
} from "@/lib/api";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
  Filler,
);

const axisColor = "rgba(51, 65, 85, 0.75)";
const tickColor = "#94a3b8";
const tooltipBg = "rgba(15, 23, 42, 0.96)";
const palette = {
  sky: "#38bdf8",
  cyan: "#22d3ee",
  emerald: "#34d399",
  violet: "#a78bfa",
  amber: "#fbbf24",
  rose: "#fb7185",
};

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { labels: { color: tickColor } },
    tooltip: {
      backgroundColor: tooltipBg,
      titleColor: "#e2e8f0",
      bodyColor: "#cbd5e1",
      borderColor: axisColor,
      borderWidth: 1,
    },
  },
};

const scaleOptions = {
  x: { grid: { color: axisColor }, ticks: { color: tickColor } },
  y: { grid: { color: axisColor }, ticks: { color: tickColor } },
};

export function AnalyticsDashboard() {
  const taskQuery = useQuery({
    queryKey: ["task-analytics"],
    queryFn: () => getTaskAnalytics(),
    refetchInterval: 10000,
  });
  const runtimeQuery = useQuery({
    queryKey: ["runtime-analytics"],
    queryFn: () => getRuntimeAnalytics(),
    refetchInterval: 10000,
  });
  const healthQueries = useQueries({
    queries: platformServices.map((s) => ({
      queryKey: ["service-health", s.name],
      queryFn: () => getServiceHealth(s),
    })),
  });

  const task = taskQuery.data;
  const runtime = runtimeQuery.data;
  const healthEntries = platformServices.map((s, i) => ({
    ...s,
    health: healthQueries[i]?.data ?? null,
  }));

  return (
    <div className="space-y-8">
      {/* Task Execution */}
      <section>
        <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold text-slate-100">
          <BarChart3 className="h-5 w-5 text-sky-400" />
          任务执行
        </h2>
        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          <Card className="border-slate-800 bg-slate-900/50">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-base">
                <PieChart className="h-4 w-4 text-sky-400" />
                任务状态分布
              </CardTitle>
              <CardDescription>按状态分类的任务数量</CardDescription>
            </CardHeader>
            <CardContent className="h-[280px]">
              <Doughnut
                data={{
                  labels: task?.status_breakdown.map((p) => p.label) ?? [],
                  datasets: [
                    {
                      data: task?.status_breakdown.map((p) => p.value) ?? [],
                      backgroundColor: [palette.sky, palette.emerald, palette.amber, palette.violet, palette.rose],
                      borderColor: "rgba(15, 23, 42, 0.96)",
                      borderWidth: 2,
                      hoverOffset: 8,
                    },
                  ],
                }}
                options={chartOptions}
              />
            </CardContent>
          </Card>

          <Card className="border-slate-800 bg-slate-900/50 xl:col-span-2">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-base">
                <TrendingUp className="h-4 w-4 text-sky-400" />
                任务执行趋势
              </CardTitle>
              <CardDescription>近 7 天任务创建量</CardDescription>
            </CardHeader>
            <CardContent className="h-[280px]">
              <Line
                data={{
                  labels: task?.recent_task_volume.map((p) => p.label) ?? [],
                  datasets: [
                    {
                      label: "任务量",
                      data: task?.recent_task_volume.map((p) => p.value) ?? [],
                      borderColor: palette.sky,
                      backgroundColor: "rgba(56, 189, 248, 0.12)",
                      fill: true,
                      tension: 0.35,
                      pointBackgroundColor: palette.sky,
                    },
                  ],
                }}
                options={{ ...chartOptions, scales: scaleOptions }}
              />
            </CardContent>
          </Card>

          <Card className="border-slate-800 bg-slate-900/50 xl:col-span-3">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-base">
                执行耗时对比
              </CardTitle>
              <CardDescription>任务侧 vs Runtime 侧执行时长（秒）</CardDescription>
            </CardHeader>
            <CardContent className="h-[260px]">
              <Bar
                data={{
                  labels: task?.execution_time_breakdown.map((p) => p.label) ?? [],
                  datasets: [
                    {
                      label: "任务耗时",
                      data: task?.execution_time_breakdown.map((p) => p.value) ?? [],
                      backgroundColor: palette.violet,
                      borderRadius: 6,
                    },
                    {
                      label: "Runtime 耗时",
                      data: runtime?.execution_time_breakdown.map((p) => p.value) ?? [],
                      backgroundColor: palette.emerald,
                      borderRadius: 6,
                    },
                  ],
                }}
                options={{ ...chartOptions, scales: scaleOptions }}
              />
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Agent Performance */}
      <section>
        <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold text-slate-100">
          <Cpu className="h-5 w-5 text-emerald-400" />
          Agent 性能
        </h2>
        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          <Card className="border-slate-800 bg-slate-900/50">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-base">
                Agent 成功率
              </CardTitle>
              <CardDescription>已完成 / 失败运行数</CardDescription>
            </CardHeader>
            <CardContent className="h-[280px]">
              <Doughnut
                data={{
                  labels: ["成功", "失败"],
                  datasets: [
                    {
                      data: [runtime?.successful_runs ?? 0, runtime?.failed_runs ?? 0],
                      backgroundColor: [palette.emerald, palette.rose],
                      borderColor: "rgba(15, 23, 42, 0.96)",
                      borderWidth: 2,
                      hoverOffset: 8,
                    },
                  ],
                }}
                options={chartOptions}
              />
            </CardContent>
          </Card>

          <Card className="border-slate-800 bg-slate-900/50 xl:col-span-2">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-base">
                <Sigma className="h-4 w-4 text-emerald-400" />
                Token 用量
              </CardTitle>
              <CardDescription>输入、输出与总 Token 消耗</CardDescription>
            </CardHeader>
            <CardContent className="h-[280px]">
              <Bar
                data={{
                  labels: ["输入 Token", "输出 Token", "总 Token"],
                  datasets: [
                    {
                      label: "Token 数",
                      data: [
                        runtime?.prompt_tokens_total ?? 0,
                        runtime?.completion_tokens_total ?? 0,
                        runtime?.total_tokens_total ?? 0,
                      ],
                      backgroundColor: [palette.sky, palette.violet, palette.emerald],
                      borderRadius: 6,
                    },
                  ],
                }}
                options={{ ...chartOptions, scales: scaleOptions }}
              />
            </CardContent>
          </Card>

          <Card className="border-slate-800 bg-slate-900/50 xl:col-span-3">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-base">
                Provider 分布
              </CardTitle>
              <CardDescription>按模型 Provider 的运行分布</CardDescription>
            </CardHeader>
            <CardContent className="h-[220px]">
              <Bar
                data={{
                  labels: runtime?.provider_breakdown.map((p) => p.label) ?? [],
                  datasets: [
                    {
                      label: "运行数",
                      data: runtime?.provider_breakdown.map((p) => p.value) ?? [],
                      backgroundColor: palette.cyan,
                      borderRadius: 6,
                    },
                  ],
                }}
                options={{ ...chartOptions, scales: scaleOptions }}
              />
            </CardContent>
          </Card>
        </div>
      </section>

      {/* System Usage */}
      <section>
        <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold text-slate-100">
          <Server className="h-5 w-5 text-violet-400" />
          系统使用
        </h2>
        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          <Card className="border-slate-800 bg-slate-900/50">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-base">
                服务健康
              </CardTitle>
              <CardDescription>平台各服务运行状态</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {healthEntries.map((s) => (
                  <div
                    key={s.name}
                    className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/80 px-4 py-3"
                  >
                    <span className="text-sm font-medium text-slate-200">{s.name}</span>
                    <StatusBadge value={s.health?.status ?? "unreachable"} />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="border-slate-800 bg-slate-900/50">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-base">
                核心指标
              </CardTitle>
              <CardDescription>任务与 Agent 汇总</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="rounded-xl border border-slate-800 bg-slate-950/80 p-4">
                <p className="text-xs text-slate-500">任务成功率</p>
                <p className="mt-1 text-2xl font-semibold text-slate-100">
                  {((task?.agent_success_rate ?? 0) * 100).toFixed(1)}%
                </p>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-950/80 p-4">
                <p className="text-xs text-slate-500">平均执行时长</p>
                <p className="mt-1 text-2xl font-semibold text-slate-100">
                  {(task?.average_execution_time_seconds ?? 0).toFixed(1)}s
                </p>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-950/80 p-4">
                <p className="text-xs text-slate-500">总 Token 消耗</p>
                <p className="mt-1 text-2xl font-semibold text-slate-100">
                  {((runtime?.total_tokens_total ?? 0) / 1000).toFixed(1)}k
                </p>
              </div>
            </CardContent>
          </Card>

          <Card className="border-slate-800 bg-slate-900/50">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-base">
                近期 Token 用量
              </CardTitle>
              <CardDescription>最近运行的 Token 消耗趋势</CardDescription>
            </CardHeader>
            <CardContent className="h-[280px]">
              <Line
                data={{
                  labels: runtime?.recent_token_usage.map((p) => p.label) ?? [],
                  datasets: [
                    {
                      label: "Token",
                      data: runtime?.recent_token_usage.map((p) => p.value) ?? [],
                      borderColor: palette.violet,
                      backgroundColor: "rgba(167, 139, 250, 0.12)",
                      fill: true,
                      tension: 0.35,
                    },
                  ],
                }}
                options={{ ...chartOptions, scales: scaleOptions }}
              />
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  );
}
