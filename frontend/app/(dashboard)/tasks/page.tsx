"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ListTodo, Play, Search, Square, Workflow } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import {
  DataCell,
  DataRow,
  DataTable,
  FilterBar,
  HeroTip,
  MetricCard,
  PageHero,
  PanelHeader,
  selectClassName,
  TableShell
} from "@/components/shared/admin-kit";
import { EmptyState } from "@/components/shared/empty-state";
import { StatusBadge } from "@/components/shared/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { cancelTask, createTask, listAgents, listProjects, listTasks, listWorkflows, runTask } from "@/lib/api";

export default function TasksPage() {
  const queryClient = useQueryClient();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [projectId, setProjectId] = useState("");
  const [agentId, setAgentId] = useState("");
  const [workflowId, setWorkflowId] = useState("");
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [keyword, setKeyword] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const tasksQuery = useQuery({
    queryKey: ["tasks"],
    queryFn: () => listTasks()
  });
  const projectsQuery = useQuery({
    queryKey: ["projects"],
    queryFn: () => listProjects()
  });
  const agentsQuery = useQuery({
    queryKey: ["agents"],
    queryFn: () => listAgents()
  });
  const workflowsQuery = useQuery({
    queryKey: ["workflows"],
    queryFn: () => listWorkflows()
  });

  const defaultProjectId = useMemo(() => projectsQuery.data?.[0]?.id ?? "", [projectsQuery.data]);
  const selectedTask = useMemo(
    () => (tasksQuery.data ?? []).find((task) => task.id === selectedTaskId) ?? tasksQuery.data?.[0] ?? null,
    [selectedTaskId, tasksQuery.data]
  );
  const filteredTasks = useMemo(
    () =>
      (tasksQuery.data ?? []).filter((task) => {
        const matchesKeyword =
          !keyword.trim() ||
          task.title.toLowerCase().includes(keyword.toLowerCase()) ||
          (task.description ?? "").toLowerCase().includes(keyword.toLowerCase());
        const matchesStatus = statusFilter === "all" || task.status === statusFilter;
        return matchesKeyword && matchesStatus;
      }),
    [keyword, statusFilter, tasksQuery.data]
  );

  useEffect(() => {
    if (!selectedTaskId && tasksQuery.data?.[0]?.id) {
      setSelectedTaskId(tasksQuery.data[0].id);
    }
  }, [selectedTaskId, tasksQuery.data]);

  const createTaskMutation = useMutation({
    mutationFn: createTask,
    onSuccess: () => {
      setTitle("");
      setDescription("");
      setAgentId("");
      setWorkflowId("");
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
    }
  });

  const runTaskMutation = useMutation({
    mutationFn: runTask,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
    }
  });

  const cancelTaskMutation = useMutation({
    mutationFn: cancelTask,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
    }
  });

  return (
    <div className="space-y-6">
      <PageHero
        eyebrow="任务调度与执行中心"
        title="统一发起任务、分配智能员工，并跟踪重试与执行结果"
        description="布局参考国内常见 SaaS 任务后台，重点突出新建投递、状态筛选、表格检索和右侧详情追踪。"
      >
        <HeroTip label="建议动作" value="高优任务建议绑定标准流程，减少人工介入。" />
        <HeroTip label="关注重点" value="重点观察失败任务和重试窗口消耗。" />
      </PageHero>

      <section className="grid gap-4 md:grid-cols-3">
        <MetricCard label="任务总数" value={String(tasksQuery.data?.length ?? 0)} />
        <MetricCard label="待处理队列" value={String((tasksQuery.data ?? []).filter((task) => task.status === "pending").length)} />
        <MetricCard label="执行中任务" value={String((tasksQuery.data ?? []).filter((task) => task.status === "running").length)} />
      </section>

      <FilterBar title="筛选与检索" description="支持按任务名称、说明和状态快速定位当前队列。">
        <div className="relative min-w-[260px] flex-1">
          <Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-slate-400" />
          <Input className="pl-9" value={keyword} onChange={(event) => setKeyword(event.target.value)} placeholder="搜索任务标题或说明" />
        </div>
        <select className={`${selectClassName} max-w-[180px]`} value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
          <option value="all">全部状态</option>
          <option value="pending">待处理</option>
          <option value="running">执行中</option>
          <option value="completed">已完成</option>
          <option value="failed">失败</option>
        </select>
      </FilterBar>

      <section className="grid gap-6 xl:grid-cols-[400px_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>新建任务</CardTitle>
            <CardDescription>将新的业务需求投递到 Agent Runtime 与流程执行队列。</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm text-slate-300">所属项目</label>
              <select className={selectClassName} value={projectId || defaultProjectId} onChange={(event) => setProjectId(event.target.value)}>
                {(projectsQuery.data ?? []).map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-300">任务标题</label>
              <Input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="撰写新品发布会预热文案" />
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-300">任务说明</label>
              <Textarea
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="请输入交付目标、投放渠道、上下游依赖和完成标准。"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-300">指派智能员工</label>
              <select className={selectClassName} value={agentId} onChange={(event) => setAgentId(event.target.value)}>
                <option value="">暂不指派</option>
                {(agentsQuery.data ?? []).map((agent) => (
                  <option key={agent.id} value={agent.id}>
                    {agent.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-300">关联流程</label>
              <select className={selectClassName} value={workflowId} onChange={(event) => setWorkflowId(event.target.value)}>
                <option value="">不绑定流程</option>
                {(workflowsQuery.data ?? []).map((workflow) => (
                  <option key={workflow.id} value={workflow.id}>
                    {workflow.name}
                  </option>
                ))}
              </select>
            </div>
            <Button
              className="w-full"
              disabled={!title.trim() || createTaskMutation.isPending}
              onClick={() =>
                createTaskMutation.mutate({
                  projectId: projectId || defaultProjectId,
                  title,
                  description,
                  agentId: agentId || undefined,
                  workflowId: workflowId || undefined
                })
              }
            >
              {createTaskMutation.isPending ? "创建中..." : "立即创建任务"}
            </Button>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <TableShell>
            <div className="p-6">
              <PanelHeader title="任务队列表格" description="集中监控任务状态、重试次数和流程路由情况。" />
              {filteredTasks.length === 0 ? (
                <EmptyState
                  title="暂无任务"
                  description="创建任务后，业务需求会进入执行链路并在这里持续跟踪。"
                  icon={ListTodo}
                />
              ) : (
                <DataTable headers={["任务标题", "状态", "优先级", "重试", "流程", "操作"]}>
                  {filteredTasks.map((task) => (
                    <DataRow key={task.id} selected={selectedTask?.id === task.id} onClick={() => setSelectedTaskId(task.id)}>
                      <DataCell>
                        <div>
                          <p className="font-medium text-slate-100">{task.title}</p>
                          <p className="mt-1 text-xs text-slate-400">{task.description}</p>
                        </div>
                      </DataCell>
                      <DataCell>
                        <StatusBadge value={task.status} />
                      </DataCell>
                      <DataCell>
                        <StatusBadge value={task.priority} />
                      </DataCell>
                      <DataCell>
                        {task.attempt_count}/{task.max_attempts}
                      </DataCell>
                      <DataCell>
                        <div className="flex items-center gap-2 text-slate-300">
                          <Workflow className="h-4 w-4 text-sky-300" />
                          <span>{task.workflow_id ? "已绑定流程" : "独立任务"}</span>
                        </div>
                      </DataCell>
                      <DataCell className="min-w-[180px]">
                        <div className="flex flex-wrap gap-2">
                          <Button
                            size="sm"
                            variant="secondary"
                            disabled={runTaskMutation.isPending}
                            onClick={(event) => {
                              event.stopPropagation();
                              runTaskMutation.mutate(task.id);
                            }}
                          >
                            <Play className="mr-2 h-4 w-4" />
                            运行
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            disabled={cancelTaskMutation.isPending}
                            onClick={(event) => {
                              event.stopPropagation();
                              cancelTaskMutation.mutate(task.id);
                            }}
                          >
                            <Square className="mr-2 h-4 w-4" />
                            取消
                          </Button>
                        </div>
                      </DataCell>
                    </DataRow>
                  ))}
                </DataTable>
              )}
            </div>
          </TableShell>

          {selectedTask ? (
            <Card>
              <CardHeader>
                <CardTitle>任务详情</CardTitle>
                <CardDescription>查看当前任务的分配关系、重试策略和交付元数据。</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4 md:grid-cols-2">
                <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                  <p className="text-sm text-slate-400">当前状态</p>
                  <div className="mt-3">
                    <StatusBadge value={selectedTask.status} />
                  </div>
                </div>
                <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                  <p className="text-sm text-slate-400">重试窗口</p>
                  <p className="mt-2 text-lg font-semibold text-slate-100">
                    {selectedTask.attempt_count} / {selectedTask.max_attempts}
                  </p>
                </div>
                <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                  <p className="text-sm text-slate-400">指派智能员工</p>
                  <p className="mt-2 text-sm text-slate-100">{selectedTask.agent_id ?? "未指派"}</p>
                </div>
                <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                  <p className="text-sm text-slate-400">关联流程</p>
                  <p className="mt-2 text-sm text-slate-100">{selectedTask.workflow_id ?? "未绑定流程"}</p>
                </div>
              </CardContent>
            </Card>
          ) : null}
        </div>
      </section>
    </div>
  );
}
