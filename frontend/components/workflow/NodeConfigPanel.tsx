"use client";

import type { Node } from "@xyflow/react";
import { Bot, Wrench, GitBranch, Timer } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const iconMap: Record<string, typeof Bot> = {
  agent_node: Bot,
  tool_node: Wrench,
  condition_node: GitBranch,
  delay_node: Timer,
};

export type NodeConfigPanelProps = {
  node: Node | null;
  agents: Array<{ id: string; name: string }>;
  onUpdate: (nodeId: string, data: Record<string, unknown>) => void;
};

export function NodeConfigPanel({ node, agents, onUpdate }: NodeConfigPanelProps) {
  if (!node) {
    return (
      <Card className="border-slate-800 bg-slate-900/50">
        <CardContent className="flex flex-col items-center justify-center py-12 text-center">
          <p className="text-sm text-slate-400">点击画布中的节点以编辑配置</p>
          <p className="mt-1 text-xs text-slate-500">或从左侧拖拽节点到画布</p>
        </CardContent>
      </Card>
    );
  }

  const nodeType = (node.type as string) || "agent_node";
  const data = (node.data || {}) as Record<string, unknown>;
  const Icon = iconMap[nodeType] ?? Bot;

  const handleChange = (key: string, value: unknown) => {
    onUpdate(node.id, { ...data, [key]: value });
  };

  return (
    <Card className="border-slate-800 bg-slate-900/50">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <Icon className="h-4 w-4 text-sky-400" />
          {nodeType.replace("_node", "")} 配置
        </CardTitle>
        <CardDescription>编辑节点属性与执行参数</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label>节点名称</Label>
          <Input
            value={(data.name as string) || ""}
            onChange={(e) => handleChange("name", e.target.value)}
            placeholder="节点显示名称"
          />
        </div>

        {nodeType === "agent_node" && (
          <>
            <div className="space-y-2">
              <Label>关联 Agent</Label>
              <select
                className="w-full rounded-xl border border-slate-800 bg-slate-900/60 px-3 py-2 text-sm text-slate-100 focus:border-sky-400 focus:outline-none focus:ring-4 focus:ring-sky-500/20"
                value={(data.assigned_agent_id as string) || ""}
                onChange={(e) => handleChange("assigned_agent_id", e.target.value || null)}
              >
                <option value="">选择 Agent</option>
                {agents.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <Label>任务标题</Label>
              <Input
                value={(data.task_title as string) || ""}
                onChange={(e) => handleChange("task_title", e.target.value)}
                placeholder="任务标题"
              />
            </div>
            <div className="space-y-2">
              <Label>任务描述</Label>
              <Input
                value={(data.task_description as string) || ""}
                onChange={(e) => handleChange("task_description", e.target.value)}
                placeholder="任务描述"
              />
            </div>
          </>
        )}

        {nodeType === "tool_node" && (
          <>
            <div className="space-y-2">
              <Label>工具名称</Label>
              <select
                className="w-full rounded-xl border border-slate-800 bg-slate-900/60 px-3 py-2 text-sm text-slate-100 focus:border-sky-400 focus:outline-none focus:ring-4 focus:ring-sky-500/20"
                value={(data.tool_name as string) || "wordpress"}
                onChange={(e) => handleChange("tool_name", e.target.value)}
              >
                <option value="wordpress">WordPress</option>
                <option value="facebook">Facebook</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label>操作</Label>
              <select
                className="w-full rounded-xl border border-slate-800 bg-slate-900/60 px-3 py-2 text-sm text-slate-100 focus:border-sky-400 focus:outline-none focus:ring-4 focus:ring-sky-500/20"
                value={(data.action as string) || (data.tool_name === "facebook" ? "create_post" : "publish_post")}
                onChange={(e) => handleChange("action", e.target.value)}
              >
                {(data.tool_name as string) === "facebook" ? (
                  <>
                    <option value="create_post">创建帖子</option>
                    <option value="comment_post">评论帖子</option>
                    <option value="send_message">发送消息</option>
                  </>
                ) : (
                  <>
                    <option value="publish_post">发布文章</option>
                    <option value="update_post">更新文章</option>
                    <option value="delete_post">删除文章</option>
                  </>
                )}
              </select>
            </div>
          </>
        )}

        {nodeType === "condition_node" && (
          <>
            <div className="space-y-2">
              <Label>上下文路径 (key)</Label>
              <Input
                value={(data.key as string) || ""}
                onChange={(e) => handleChange("key", e.target.value)}
                placeholder="例如: input.channel"
              />
            </div>
            <div className="space-y-2">
              <Label>期望值 (equals)</Label>
              <Input
                value={(data.equals as string) || ""}
                onChange={(e) => handleChange("equals", e.target.value)}
                placeholder="匹配时继续"
              />
            </div>
          </>
        )}

        {nodeType === "delay_node" && (
          <div className="space-y-2">
            <Label>延时秒数</Label>
            <Input
              type="number"
              min={1}
              max={300}
              value={(data.seconds as number) ?? 2}
              onChange={(e) => handleChange("seconds", parseInt(e.target.value, 10) || 1)}
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
