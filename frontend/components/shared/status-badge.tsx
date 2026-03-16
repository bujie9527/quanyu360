"use client";

import { Badge } from "@/components/ui/badge";

type StatusBadgeProps = {
  value: string;
};

const variantMap: Record<string, "default" | "success" | "warning" | "outline"> = {
  active: "success",
  completed: "success",
  healthy: "success",
  running: "default",
  pending: "warning",
  draft: "outline",
  unreachable: "warning",
  failed: "warning",
  cancelled: "outline",
  paused: "outline",
  idle: "outline",
  admin: "default",
  manager: "success",
  operator: "outline"
};

const labelMap: Record<string, string> = {
  active: "运行中",
  completed: "已完成",
  healthy: "健康",
  running: "执行中",
  pending: "待处理",
  draft: "草稿",
  unreachable: "不可达",
  failed: "失败",
  cancelled: "已取消",
  paused: "已暂停",
  idle: "空闲",
  admin: "管理员",
  manager: "经理",
  operator: "操作员",
  normal: "普通",
  high: "高优先级",
  manual: "手动触发",
  agent_task: "Agent 任务",
  tool_call: "工具调用",
  condition: "条件判断",
  delay: "延时"
};

export function StatusBadge({ value }: StatusBadgeProps) {
  const normalized = value.toLowerCase();
  const variant = variantMap[normalized] ?? "outline";
  const label = labelMap[normalized] ?? value;

  return <Badge variant={variant}>{label}</Badge>;
}
