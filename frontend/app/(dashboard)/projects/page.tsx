"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BriefcaseBusiness, FolderPlus, Layers3, Search, Users } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { DataCell, DataRow, DataTable, FilterBar, HeroTip, MetricCard, PageHero, PanelHeader, TableShell } from "@/components/shared/admin-kit";
import { EmptyState } from "@/components/shared/empty-state";
import { StatusBadge } from "@/components/shared/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { createProject, listProjects } from "@/lib/api";

export default function ProjectsPage() {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [projectType, setProjectType] = useState<"general" | "matrix_site">("general");
  const [brandName, setBrandName] = useState("");
  const [productCategory, setProductCategory] = useState("");
  const [targetMarket, setTargetMarket] = useState("");
  const [promotionGoal, setPromotionGoal] = useState("");
  const [targetAudience, setTargetAudience] = useState("");
  const [contentLanguages, setContentLanguages] = useState("en");
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [keyword, setKeyword] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const projectsQuery = useQuery({
    queryKey: ["projects"],
    queryFn: () => listProjects()
  });

  useEffect(() => {
    if (!selectedProjectId && projectsQuery.data?.[0]?.id) {
      setSelectedProjectId(projectsQuery.data[0].id);
    }
  }, [projectsQuery.data, selectedProjectId]);

  const createProjectMutation = useMutation({
    mutationFn: createProject,
    onSuccess: (project) => {
      setName("");
      setDescription("");
      setProjectType("general");
      setBrandName("");
      setProductCategory("");
      setTargetMarket("");
      setPromotionGoal("");
      setTargetAudience("");
      setContentLanguages("en");
      setSelectedProjectId(project.id);
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    }
  });

  const selectedProject = useMemo(
    () => (projectsQuery.data ?? []).find((project) => project.id === selectedProjectId) ?? projectsQuery.data?.[0] ?? null,
    [projectsQuery.data, selectedProjectId]
  );
  const filteredProjects = useMemo(
    () =>
      (projectsQuery.data ?? []).filter((project) => {
        const matchesKeyword =
          !keyword.trim() ||
          project.name.toLowerCase().includes(keyword.toLowerCase()) ||
          (project.description ?? "").toLowerCase().includes(keyword.toLowerCase()) ||
          project.key.toLowerCase().includes(keyword.toLowerCase());
        const matchesStatus = statusFilter === "all" || project.status === statusFilter;
        return matchesKeyword && matchesStatus;
      }),
    [keyword, projectsQuery.data, statusFilter]
  );

  return (
    <div className="space-y-6">
      <PageHero
        eyebrow="项目是企业交付与资源编排的基本单位"
        title="统一管理项目、成员、流程和交付边界"
        description=""
      >
      </PageHero>

      <section className="grid gap-4 md:grid-cols-3">
        <MetricCard label="项目总数" value={String(projectsQuery.data?.length ?? 0)} />
        <MetricCard
          label="运行中项目"
          value={String((projectsQuery.data ?? []).filter((project) => project.status === "active").length)}
        />
        <MetricCard
          label="团队成员覆盖"
          value={String((projectsQuery.data ?? []).reduce((sum, project) => sum + project.team_members.length, 0))}
        />
      </section>

      {/* <FilterBar title="筛选与检索" description="支持按项目名称、编号和状态快速定位项目。">
        <div className="relative min-w-[260px] flex-1">
          <Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-slate-400" />
          <Input className="pl-9" value={keyword} onChange={(event) => setKeyword(event.target.value)} placeholder="搜索项目名称、编号或说明" />
        </div>
        <select className="saas-select max-w-[180px]" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
          <option value="all">全部状态</option>
          <option value="active">运行中</option>
          <option value="draft">草稿</option>
        </select>
      </FilterBar> */}

      <section className="grid gap-6 xl:grid-cols-[360px_1fr]">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FolderPlus className="h-5 w-5 text-sky-300" />
              新建项目
            </CardTitle>
            <CardDescription>为业务线创建独立项目空间，统一管理 Agent、任务与流程。</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm text-slate-300">项目名称</label>
              <Input value={name} onChange={(event) => setName(event.target.value)} placeholder="增长内容运营" />
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-300">项目类型</label>
              <select
                className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
                value={projectType}
                onChange={(event) => setProjectType(event.target.value as "general" | "matrix_site")}
              >
                <option value="general">通用项目</option>
                <option value="matrix_site">矩阵建站</option>
              </select>
            </div>
            {projectType === "matrix_site" && (
              <>
                <div className="space-y-2">
                  <label className="text-sm text-slate-300">品牌名称</label>
                  <Input value={brandName} onChange={(event) => setBrandName(event.target.value)} placeholder="百潮荟" />
                </div>
                <div className="space-y-2">
                  <label className="text-sm text-slate-300">产品品类</label>
                  <Input value={productCategory} onChange={(event) => setProductCategory(event.target.value)} placeholder="潮玩/设计师玩具" />
                </div>
                <div className="space-y-2">
                  <label className="text-sm text-slate-300">目标市场</label>
                  <Input value={targetMarket} onChange={(event) => setTargetMarket(event.target.value)} placeholder="欧美" />
                </div>
                <div className="space-y-2">
                  <label className="text-sm text-slate-300">推广目标</label>
                  <Textarea value={promotionGoal} onChange={(event) => setPromotionGoal(event.target.value)} placeholder="建立品牌搜索认知，沉淀内容资产" />
                </div>
                <div className="space-y-2">
                  <label className="text-sm text-slate-300">目标人群</label>
                  <Textarea value={targetAudience} onChange={(event) => setTargetAudience(event.target.value)} placeholder="18-35 岁，收藏爱好者，偏好艺术设计和潮流文化" />
                </div>
                <div className="space-y-2">
                  <label className="text-sm text-slate-300">内容语言（逗号分隔）</label>
                  <Input value={contentLanguages} onChange={(event) => setContentLanguages(event.target.value)} placeholder="en,de,fr" />
                </div>
              </>
            )}
            <div className="space-y-2">
              <label className="text-sm text-slate-300">项目说明</label>
              <Textarea
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="请输入业务目标、执行方式、交付范围和协作模式。"
              />
            </div>
            <Button
              className="w-full"
              disabled={!name.trim() || createProjectMutation.isPending}
              onClick={() =>
                createProjectMutation.mutate({
                  name,
                  description,
                  project_type: projectType,
                  matrix_config:
                    projectType === "matrix_site"
                      ? {
                          brand_name: brandName,
                          product_category: productCategory,
                          target_market: targetMarket,
                          promotion_goal: promotionGoal,
                          target_audience: targetAudience,
                          content_languages: contentLanguages
                            .split(",")
                            .map((lang) => lang.trim())
                            .filter(Boolean),
                        }
                      : {}
                })
              }
            >
              {createProjectMutation.isPending ? "创建中..." : "立即创建项目"}
            </Button>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <TableShell>
            <div className="p-6">
              <PanelHeader title="项目列表" description="集中查看项目归属、团队配置和任务承载情况。" />
              {filteredProjects.length === 0 ? (
                <EmptyState
                  title="还没有项目"
                  description="先创建第一个项目空间，再开始组织 Agent、任务和流程资产。"
                  icon={BriefcaseBusiness}
                />
              ) : (
                <DataTable headers={["项目名称", "项目编号", "类型", "状态", "成员数", "Agent", "任务", "流程"]}>
                  {filteredProjects.map((project) => (
                    <DataRow key={project.id} selected={selectedProject?.id === project.id} onClick={() => setSelectedProjectId(project.id)}>
                      <DataCell>
                        <div>
                          <p className="font-medium text-slate-100">{project.name}</p>
                          <p className="mt-1 max-w-xl text-xs text-slate-400">{project.description}</p>
                        </div>
                      </DataCell>
                      <DataCell>{project.key}</DataCell>
                      <DataCell>
                        <StatusBadge value={project.project_type === "matrix_site" ? "matrix_site" : "general"} />
                      </DataCell>
                      <DataCell>
                        <StatusBadge value={project.status} />
                      </DataCell>
                      <DataCell>{project.team_members.length}</DataCell>
                      <DataCell>{project.agent_count}</DataCell>
                      <DataCell>{project.task_count}</DataCell>
                      <DataCell>{project.workflow_count}</DataCell>
                    </DataRow>
                  ))}
                </DataTable>
              )}
            </div>
          </TableShell>

          {selectedProject ? (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Layers3 className="h-5 w-5 text-sky-300" />
                  {selectedProject.name}
                </CardTitle>
                <CardDescription>查看当前项目的资源配置、团队成员和执行覆盖情况。</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
                    <p className="text-sm text-slate-400">已分配 Agent</p>
                    <p className="mt-2 text-2xl font-semibold text-slate-100">{selectedProject.agent_count}</p>
                  </div>
                  <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
                    <p className="text-sm text-slate-400">在列与执行中任务</p>
                    <p className="mt-2 text-2xl font-semibold text-slate-100">{selectedProject.task_count}</p>
                  </div>
                  <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
                    <p className="text-sm text-slate-400">流程模板数</p>
                    <p className="mt-2 text-2xl font-semibold text-slate-100">{selectedProject.workflow_count}</p>
                  </div>
                </div>

                <div>
                  <div className="flex items-center gap-2 text-sm text-slate-400">
                    <Users className="h-4 w-4" />
                    <span>已分配 {selectedProject.team_members.length} 位成员</span>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {selectedProject.team_members.map((member) => (
                      <div
                        key={member.user_id}
                        className="rounded-full border border-slate-700 bg-slate-900 px-3 py-1 text-xs text-slate-300"
                      >
                        {member.full_name} · {member.role}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
                  <p className="text-sm text-slate-400">项目管理建议</p>
                  <p className="mt-2 text-sm leading-6 text-slate-300">
                    建议按“业务目标、负责人、Agent 配置、流程模板、任务看板”五个维度完成项目初始化，便于后续快速复制和规模化交付。
                  </p>
                </div>
              </CardContent>
            </Card>
          ) : null}
        </div>
      </section>
    </div>
  );
}
