"use client";

import { ScrollText } from "lucide-react";

import {
  PageHero,
  PanelHeader,
  TableShell,
} from "@/components/shared/admin-kit";
import { EmptyState } from "@/components/shared/empty-state";

export default function AdminAgentLogsPage() {
  return (
    <div className="space-y-6">
      <PageHero
        eyebrow="AI员工"
        title="Agent Logs"
        description="Agent 执行日志与调用记录。"
      />

      <TableShell>
        <div className="p-6">
          <PanelHeader
            title="Agent 执行日志"
            description="查看 Agent 对话、任务执行与工具调用的日志。"
          />
          <EmptyState
            title="日志功能规划中"
            description="Agent 执行日志将对接 observability 或审计服务，敬请期待。"
            icon={ScrollText}
          />
        </div>
      </TableShell>
    </div>
  );
}
