"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowUpRight, ScrollText } from "lucide-react";
import Link from "next/link";

import { EmptyState } from "@/components/shared/empty-state";
import { StatusBadge } from "@/components/shared/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { listExecutions } from "@/lib/api";

function formatTimestamp(value: string | null) {
  if (!value) {
    return "执行中";
  }
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}

export function RecentExecutions() {
  const executionsQuery = useQuery({
    queryKey: ["executions"],
    queryFn: () => listExecutions(),
    refetchInterval: 10000
  });

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <div>
          <CardTitle>最新执行记录</CardTitle>
          <CardDescription>展示最近的工作流运行情况，并实时跟踪当前步骤状态。</CardDescription>
        </div>
        <Button asChild size="sm" variant="outline">
          <Link href="/results">
            查看全部
            <ArrowUpRight className="ml-2 h-4 w-4" />
          </Link>
        </Button>
      </CardHeader>
      <CardContent className="space-y-3">
        {(executionsQuery.data ?? []).length === 0 ? (
          <EmptyState
            title="暂无执行记录"
            description="当流程开始运行后，最近的执行日志会展示在这里。"
            icon={ScrollText}
          />
        ) : (
          (executionsQuery.data ?? []).slice(0, 4).map((execution) => (
            <div
              key={execution.execution_id}
              className="flex flex-col gap-3 rounded-2xl border border-slate-800 bg-slate-900/70 p-4 sm:flex-row sm:items-center sm:justify-between"
            >
              <div>
                <p className="font-medium text-slate-100">{execution.execution_id}</p>
                <p className="mt-1 text-sm text-slate-400">
                  流程 {execution.workflow_id} {execution.current_step ? `· 当前步骤 ${execution.current_step}` : ""}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <StatusBadge value={execution.status} />
                <span className="text-xs text-slate-500">{formatTimestamp(execution.completed_at ?? execution.started_at)}</span>
              </div>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
