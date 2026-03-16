"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bot, CheckCircle2, Loader2, Sparkles } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { approveSitePlan, createSitePlan, listProjects, listSitePlans, type SitePlan } from "@/lib/api";

function buildDraftItems(projectName: string, requirement: string): Array<{
  site_name: string;
  site_theme: string;
  target_audience: string;
  content_direction: string;
  seo_keywords: string[];
  site_structure: Record<string, unknown>;
}> {
  const core = requirement.trim() || `${projectName} 核心用户`;
  return [
    {
      site_name: `${projectName} Insight Hub`,
      site_theme: "趋势资讯站",
      target_audience: core,
      content_direction: "行业趋势、热点解读、品牌动态",
      seo_keywords: ["trend", "insight", "news", "guide"],
      site_structure: { columns: ["Trends", "News", "Insights"] },
    },
    {
      site_name: `${projectName} Review Lab`,
      site_theme: "评测对比站",
      target_audience: `${core} 中关注对比和决策的人群`,
      content_direction: "产品评测、横向对比、购买建议",
      seo_keywords: ["review", "comparison", "best", "vs"],
      site_structure: { columns: ["Reviews", "Comparisons", "Buying Guide"] },
    },
    {
      site_name: `${projectName} Culture Community`,
      site_theme: "圈层文化站",
      target_audience: `${core} 中偏社区交流和兴趣内容的人群`,
      content_direction: "文化内容、故事专题、社区活动",
      seo_keywords: ["community", "culture", "story", "collection"],
      site_structure: { columns: ["Stories", "Community", "Events"] },
    },
  ];
}

export default function MatrixPlannerPage() {
  const queryClient = useQueryClient();
  const [projectId, setProjectId] = useState("");
  const [requirement, setRequirement] = useState("");

  const projectsQuery = useQuery({
    queryKey: ["projects"],
    queryFn: () => listProjects(),
  });

  const matrixProjects = useMemo(
    () => (projectsQuery.data ?? []).filter((p) => p.project_type === "matrix_site"),
    [projectsQuery.data]
  );

  const selectedProject = useMemo(
    () => matrixProjects.find((p) => p.id === projectId) ?? null,
    [matrixProjects, projectId]
  );

  useEffect(() => {
    if (!projectId && matrixProjects[0]?.id) {
      setProjectId(matrixProjects[0].id);
    }
  }, [matrixProjects, projectId]);

  const plansQuery = useQuery({
    queryKey: ["site-plans", projectId],
    queryFn: () => listSitePlans(projectId, { limit: 50 }),
    enabled: !!projectId,
  });

  const generateMutation = useMutation({
    mutationFn: async () => {
      if (!selectedProject) throw new Error("请选择矩阵项目");
      const items = buildDraftItems(selectedProject.name, requirement);
      return createSitePlan(selectedProject.id, {
        agent_input: {
          project_id: selectedProject.id,
          project_name: selectedProject.name,
          matrix_config: selectedProject.matrix_config ?? {},
          user_requirement: requirement,
        },
        agent_output: {
          summary: "矩阵站规划草案",
          strategy: "按搜索意图分站点覆盖",
        },
        items,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["site-plans", projectId] });
    },
  });

  const approveMutation = useMutation({
    mutationFn: (planId: string) => approveSitePlan(planId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["site-plans", projectId] });
    },
  });

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm text-slate-400">矩阵建站 / 站点规划</p>
        <h1 className="text-2xl font-semibold text-slate-100">站点规划 Agent</h1>
      </div>

      <div className="grid gap-6 xl:grid-cols-[300px_1fr_380px]">
        <Card>
          <CardHeader>
            <CardTitle>项目信息</CardTitle>
            <CardDescription>选择矩阵建站项目并查看基础配置</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <select
              className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
              value={projectId}
              onChange={(e) => setProjectId(e.target.value)}
            >
              <option value="">选择项目</option>
              {matrixProjects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
            <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-3 text-xs text-slate-300">
              <pre className="whitespace-pre-wrap">
                {JSON.stringify(selectedProject?.matrix_config ?? {}, null, 2)}
              </pre>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bot className="h-5 w-5" />
              与规划 Agent 对话
            </CardTitle>
            <CardDescription>补充目标用户、推广侧重点和站点规模要求</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Textarea
              value={requirement}
              onChange={(e) => setRequirement(e.target.value)}
              placeholder="例如：重点吸引欧美潮玩收藏人群，先规划 3 个站点，分别覆盖资讯、评测、购买决策。"
              className="min-h-36"
            />
            <Button disabled={!projectId || generateMutation.isPending} onClick={() => generateMutation.mutate()}>
              {generateMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  生成中...
                </>
              ) : (
                <>
                  <Sparkles className="mr-2 h-4 w-4" />
                  生成规划方案
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>规划结果</CardTitle>
            <CardDescription>确认方案后可进入建站任务批量执行</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {(plansQuery.data?.items ?? []).map((plan: SitePlan) => (
              <div key={plan.id} className="rounded-lg border border-slate-800 bg-slate-900/50 p-3">
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-xs text-slate-400">{plan.status}</span>
                  {plan.status !== "approved" && (
                    <Button
                      size="sm"
                      variant="secondary"
                      disabled={approveMutation.isPending}
                      onClick={() => approveMutation.mutate(plan.id)}
                    >
                      <CheckCircle2 className="mr-1 h-3.5 w-3.5" />
                      确认此规划
                    </Button>
                  )}
                </div>
                <div className="space-y-2">
                  {plan.items.map((item) => (
                    <div key={item.id} className="rounded border border-slate-700 p-2">
                      <p className="text-sm font-medium text-slate-100">{item.site_name}</p>
                      <p className="text-xs text-slate-400">{item.site_theme}</p>
                      <p className="mt-1 text-xs text-slate-300">{item.target_audience}</p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
            {(plansQuery.data?.items ?? []).length === 0 && (
              <p className="text-sm text-slate-500">暂无规划方案</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
