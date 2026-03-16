"use client";

import { useQuery } from "@tanstack/react-query";
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
  Tooltip
} from "chart.js";
import { Activity, ChartColumnBig, PieChart, Sigma } from "lucide-react";
import { Bar, Doughnut, Line } from "react-chartjs-2";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getRuntimeAnalytics, getTaskAnalytics } from "@/lib/api";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, ArcElement, Tooltip, Legend, Filler);

const axisColor = "rgba(51, 65, 85, 0.75)";
const tickColor = "#94a3b8";
const tooltipBackground = "rgba(15, 23, 42, 0.96)";
const palette = {
  sky: "#38bdf8",
  cyan: "#22d3ee",
  emerald: "#34d399",
  violet: "#a78bfa",
  amber: "#fbbf24",
  rose: "#fb7185"
};

export function AnalyticsCharts() {
  const taskAnalyticsQuery = useQuery({
    queryKey: ["task-analytics"],
    queryFn: getTaskAnalytics,
    refetchInterval: 10000
  });
  const runtimeAnalyticsQuery = useQuery({
    queryKey: ["runtime-analytics"],
    queryFn: getRuntimeAnalytics,
    refetchInterval: 10000
  });

  const taskAnalytics = taskAnalyticsQuery.data;
  const runtimeAnalytics = runtimeAnalyticsQuery.data;

  return (
    <section className="grid gap-6 xl:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <PieChart className="h-5 w-5 text-sky-300" />
            任务状态分布
          </CardTitle>
          <CardDescription>从待处理到完成的任务结构一目了然，适合运营同学快速判断当前负载。</CardDescription>
        </CardHeader>
        <CardContent className="h-[320px]">
          <Doughnut
            data={{
              labels: taskAnalytics?.status_breakdown.map((point) => point.label) ?? [],
              datasets: [
                {
                  label: "任务数",
                  data: taskAnalytics?.status_breakdown.map((point) => point.value) ?? [],
                  backgroundColor: [palette.sky, palette.emerald, palette.amber, palette.violet, palette.rose],
                  borderColor: "rgba(15, 23, 42, 0.96)",
                  borderWidth: 2,
                  hoverOffset: 10
                }
              ]
            }}
            options={{
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: {
                  labels: { color: tickColor }
                },
                tooltip: {
                  backgroundColor: tooltipBackground,
                  titleColor: "#e2e8f0",
                  bodyColor: "#cbd5e1",
                  borderColor: axisColor,
                  borderWidth: 1
                }
              }
            }}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-sky-300" />
            任务执行趋势
          </CardTitle>
          <CardDescription>近 7 天任务创建与投递趋势，用于识别高峰时段和投放节奏。</CardDescription>
        </CardHeader>
        <CardContent className="h-[320px]">
          <Line
            data={{
              labels: taskAnalytics?.recent_task_volume.map((point) => point.label) ?? [],
              datasets: [
                {
                  label: "任务量",
                  data: taskAnalytics?.recent_task_volume.map((point) => point.value) ?? [],
                  borderColor: palette.sky,
                  backgroundColor: "rgba(56, 189, 248, 0.16)",
                  pointBackgroundColor: palette.sky,
                  pointBorderColor: "#0f172a",
                  pointHoverRadius: 5,
                  fill: true,
                  tension: 0.35
                }
              ]
            }}
            options={{
              responsive: true,
              maintainAspectRatio: false,
              scales: {
                x: {
                  grid: { color: axisColor },
                  ticks: { color: tickColor }
                },
                y: {
                  grid: { color: axisColor },
                  ticks: { color: tickColor }
                }
              },
              plugins: {
                legend: {
                  labels: { color: tickColor }
                },
                tooltip: {
                  backgroundColor: tooltipBackground,
                  titleColor: "#e2e8f0",
                  bodyColor: "#cbd5e1",
                  borderColor: axisColor,
                  borderWidth: 1
                }
              }
            }}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ChartColumnBig className="h-5 w-5 text-sky-300" />
            执行耗时对比
          </CardTitle>
          <CardDescription>对比任务侧与 Runtime 侧耗时，帮助定位性能瓶颈和链路延迟。</CardDescription>
        </CardHeader>
        <CardContent className="h-[320px]">
          <Bar
            data={{
              labels: taskAnalytics?.execution_time_breakdown.map((point) => point.label) ?? [],
              datasets: [
                {
                  label: "任务耗时（秒）",
                  data: taskAnalytics?.execution_time_breakdown.map((point) => point.value) ?? [],
                  backgroundColor: palette.violet,
                  borderRadius: 8
                },
                {
                  label: "Runtime 耗时（秒）",
                  data: runtimeAnalytics?.execution_time_breakdown.map((point) => point.value) ?? [],
                  backgroundColor: palette.emerald,
                  borderRadius: 8
                }
              ]
            }}
            options={{
              responsive: true,
              maintainAspectRatio: false,
              scales: {
                x: {
                  grid: { color: axisColor },
                  ticks: { color: tickColor }
                },
                y: {
                  grid: { color: axisColor },
                  ticks: { color: tickColor }
                }
              },
              plugins: {
                legend: {
                  labels: { color: tickColor }
                },
                tooltip: {
                  backgroundColor: tooltipBackground,
                  titleColor: "#e2e8f0",
                  bodyColor: "#cbd5e1",
                  borderColor: axisColor,
                  borderWidth: 1
                }
              }
            }}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sigma className="h-5 w-5 text-sky-300" />
            Token 用量
          </CardTitle>
          <CardDescription>持续观察输入输出消耗，为模型预算和成本控制提供依据。</CardDescription>
        </CardHeader>
        <CardContent className="h-[320px]">
          <Bar
            data={{
              labels: ["输入", "输出", "总量"],
              datasets: [
                {
                  label: "Token 数",
                  data: runtimeAnalytics
                    ? [
                        runtimeAnalytics.prompt_tokens_total,
                        runtimeAnalytics.completion_tokens_total,
                        runtimeAnalytics.total_tokens_total
                      ]
                    : [],
                  backgroundColor: [palette.sky, palette.violet, palette.emerald],
                  borderRadius: 8
                }
              ]
            }}
            options={{
              responsive: true,
              maintainAspectRatio: false,
              scales: {
                x: {
                  grid: { color: axisColor },
                  ticks: { color: tickColor }
                },
                y: {
                  grid: { color: axisColor },
                  ticks: { color: tickColor }
                }
              },
              plugins: {
                legend: {
                  labels: { color: tickColor }
                },
                tooltip: {
                  backgroundColor: tooltipBackground,
                  titleColor: "#e2e8f0",
                  bodyColor: "#cbd5e1",
                  borderColor: axisColor,
                  borderWidth: 1
                }
              }
            }}
          />
        </CardContent>
      </Card>
    </section>
  );
}
