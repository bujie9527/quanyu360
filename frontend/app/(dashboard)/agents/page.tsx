"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bot, BookOpen, FileText, Loader2, Plus, Wrench } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { EmptyState } from "@/components/shared/empty-state";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { MetricCard, PageHero } from "@/components/shared/admin-kit";
import {
  createAgentInstanceFromTemplate,
  getAgentInstance,
  listAgentInstances,
  listAgentTemplates,
  listProjectKnowledgeBases,
  listProjects,
  updateAgentInstance,
  type AgentInstanceItem,
  type AgentTemplateItem,
} from "@/lib/api";

const TABS = [
  { id: "identity", label: "身份设定" },
  { id: "core", label: "灵魂核心" },
  { id: "behavior", label: "行为规范" },
  { id: "tools", label: "工具提示" },
  { id: "user", label: "用户画像" },
  { id: "edit", label: "基础信息编辑" },
] as const;

function getInitial(name: string): string {
  const trimmed = (name ?? "").trim();
  if (!trimmed) return "?";
  // 优先取首字（支持中文）
  const first = trimmed[0];
  return first.toUpperCase();
}

export default function AgentsPage() {
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<(typeof TABS)[number]["id"]>("identity");
  const [showCreateFromTemplate, setShowCreateFromTemplate] = useState(false);
  const [templateForm, setTemplateForm] = useState({ templateId: "", projectId: "", name: "" });

  const projectsQuery = useQuery({ queryKey: ["projects"], queryFn: listProjects });
  const instancesQuery = useQuery({
    queryKey: ["agent-instances"],
    queryFn: () => listAgentInstances({ limit: 200 }),
  });
  const templatesQuery = useQuery({
    queryKey: ["agent-templates"],
    queryFn: () => listAgentTemplates({ enabled: true, limit: 100 }),
  });

  const instanceDetailQuery = useQuery({
    queryKey: ["agent-instance", selectedId],
    queryFn: () => getAgentInstance(selectedId!),
    enabled: !!selectedId,
  });

  const defaultProjectId = useMemo(() => projectsQuery.data?.[0]?.id ?? "", [projectsQuery.data]);
  const templates = (templatesQuery.data?.items ?? []) as AgentTemplateItem[];
  const instances = (instancesQuery.data?.items ?? []) as AgentInstanceItem[];
  const selectedInstance = instances.find((i) => i.id === selectedId) ?? null;
  const detail = instanceDetailQuery.data;

  useEffect(() => {
    if (!selectedId && instances[0]?.id) setSelectedId(instances[0].id);
  }, [instances, selectedId]);

  const createFromTemplateMutation = useMutation({
    mutationFn: createAgentInstanceFromTemplate,
    onSuccess: (created) => {
      queryClient.invalidateQueries({ queryKey: ["agent-instances"] });
      setShowCreateFromTemplate(false);
      setTemplateForm({ templateId: "", projectId: "", name: "" });
      setSelectedId(created.id);
    },
  });

  const projectId = detail?.project_id ?? selectedInstance?.project_id ?? "";
  const kbsQuery = useQuery({
    queryKey: ["project-knowledge-bases", projectId],
    queryFn: () => listProjectKnowledgeBases(projectId),
    enabled: !!projectId,
  });
  const kbs = kbsQuery.data ?? [];

  const [editForm, setEditForm] = useState({
    name: "",
    description: "",
    system_prompt: "",
    configJson: "{}",
    model: "",
    knowledge_base_id: "",
  });

  useEffect(() => {
    if (detail) {
      setEditForm({
        name: detail.name ?? "",
        description: detail.description ?? "",
        system_prompt: detail.system_prompt ?? "",
        configJson: detail.config ? JSON.stringify(detail.config, null, 2) : "{}",
        model: detail.model ?? "",
        knowledge_base_id: detail.knowledge_base_id ?? "",
      });
    }
  }, [detail?.id, detail?.name, detail?.description, detail?.system_prompt, detail?.config, detail?.model, detail?.knowledge_base_id]);

  const updateMutation = useMutation({
    mutationFn: (payload: Parameters<typeof updateAgentInstance>[1]) =>
      updateAgentInstance(selectedId!, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agent-instance", selectedId] });
      queryClient.invalidateQueries({ queryKey: ["agent-instances"] });
    },
  });

  const handleSaveEdit = () => {
    let config: Record<string, unknown> = {};
    try {
      config = JSON.parse(editForm.configJson || "{}");
    } catch {
      return;
    }
    updateMutation.mutate({
      name: editForm.name.trim() || undefined,
      description: editForm.description || null,
      system_prompt: editForm.system_prompt,
      model: editForm.model.trim() || undefined,
      knowledge_base_id: editForm.knowledge_base_id || null,
      config,
    });
  };

  return (
    <div className="space-y-6">
      <PageHero
        eyebrow="智能员工配置中心"
        title="按岗位职责配置智能员工，形成可复用的 AI 人力资产"
        description=""
      >
        {/* <Button variant="secondary" className="gap-2" onClick={() => setShowCreateFromTemplate(true)}>
          <FileText className="h-4 w-4" />
          从模板创建
        </Button> */}
      </PageHero>

      <section className="grid gap-4 md:grid-cols-3">
        <MetricCard label="从模板创建的智能员工" value={String(instances.length)} />
        <MetricCard
          label="可用模板数"
          value={String(templates.length)}
        />
        <MetricCard label="项目数" value={String(projectsQuery.data?.length ?? 0)} />
      </section>

      <section className="grid gap-6 xl:grid-cols-[340px_1fr]">
        {/* 左侧：从模板创建的智能员工列表 */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <div>
              <CardTitle>Agent 列表</CardTitle>
              <CardDescription>选中后即可查看Persona文件并编辑元数据。</CardDescription>
            </div>
            <Button variant="outline" size="sm" className="h-7 w-9 p-0 bg-sky-600/80 rounded-full" onClick={() => setShowCreateFromTemplate(true)}>
              <Plus className="h-4 w-4" />
            </Button>
          </CardHeader>
          <CardContent>
            {instances.length === 0 ? (
              <EmptyState
                title="暂无智能员工"
                description="点击上方按钮从模板创建第一个智能员工。"
                icon={Bot}
              />
            ) : (
              <ul className="space-y-1">
                {instances.map((inst) => (
                  <li
                    key={inst.id}
                    onClick={() => setSelectedId(inst.id)}
                    className={`flex cursor-pointer items-center gap-3 rounded-lg border px-3 py-2.5 transition-colors ${
                      selectedId === inst.id
                        ? "border-sky-500/50 bg-sky-500/10"
                        : "border-slate-800 bg-slate-900/50 hover:border-slate-700 hover:bg-slate-800/50"
                    }`}
                  >
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-sky-600/80 text-sm font-medium text-white">
                      {getInitial(inst.name)}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-medium text-slate-100">{inst.name}</p>
                      <p className="truncate text-xs text-slate-400">{inst.project_name ?? "-"}</p>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        {/* 右侧：人格 / 提示词文件详情 */}
        <Card>
          <CardHeader>
            <CardTitle>人格 / 提示词文件</CardTitle>
            <CardDescription>
              {selectedInstance
                ? `当前 Agent: ${selectedInstance.name}`
                : "请在左侧选择一个 Agent 查看详情"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {!selectedInstance ? (
              <EmptyState
                title="未选择 Agent"
                description="请在左侧列表中点击一个智能员工以查看其人格设定与提示词配置。"
                icon={BookOpen}
              />
            ) : instanceDetailQuery.isLoading && !detail ? (
              <div className="flex min-h-[200px] items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-slate-500" />
              </div>
            ) : (
              <>
                {/* 选中 Agent 摘要 */}
                <div className="mb-6 flex items-center gap-3 rounded-xl border border-slate-800 bg-slate-900/50 p-4">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-sky-600/80 text-lg font-medium text-white">
                    {getInitial(selectedInstance?.name ?? "")}
                  </div>
                  <div>
                    <p className="font-medium text-slate-100">{selectedInstance?.name}</p>
                    <p className="text-sm text-slate-400">{selectedInstance?.project_name ?? "-"}</p>
                  </div>
                </div>

                {/* 标签页 */}
                <div className="mb-4 flex flex-wrap gap-2 border-b border-slate-800 pb-3">
                  {TABS.map((t) => (
                    <button
                      key={t.id}
                      onClick={() => setActiveTab(t.id)}
                      className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                        activeTab === t.id
                          ? "bg-sky-600/80 text-white"
                          : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
                      }`}
                    >
                      {t.label}
                    </button>
                  ))}
                </div>

                {/* 内容区 */}
                <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
                  {activeTab === "identity" && (
                    <div className="space-y-4 text-sm">
                      <div>
                        <span className="text-slate-400">Name:</span>{" "}
                        <span className="text-slate-100">{detail?.name ?? selectedInstance?.name ?? "-"}</span>
                      </div>
                      <div>
                        <span className="text-slate-400">Creature / 角色:</span>{" "}
                        <span className="text-slate-100">{detail?.template_name ?? "-"}</span>
                      </div>
                      <div>
                        <span className="text-slate-400">项目:</span>{" "}
                        <span className="text-slate-100">{detail?.project_name ?? selectedInstance?.project_name ?? "-"}</span>
                      </div>
                      <div>
                        <span className="text-slate-400">描述 (Description):</span>
                        <p className="mt-1 text-slate-300">{detail?.description || "-"}</p>
                      </div>
                    </div>
                  )}
                  {activeTab === "core" && (
                    <div className="space-y-2">
                      <span className="text-slate-400">灵魂核心 - 系统提示词 (System Prompt)</span>
                      <pre className="mt-2 max-h-[400px] overflow-auto rounded-lg bg-slate-950 p-4 text-sm leading-6 text-slate-300 whitespace-pre-wrap">
                        {detail?.system_prompt || "-"}
                      </pre>
                    </div>
                  )}
                  {activeTab === "behavior" && (
                    <div className="space-y-2">
                      <span className="text-slate-400">行为规范 (Config)</span>
                      <pre className="mt-2 max-h-[400px] overflow-auto rounded-lg bg-slate-950 p-4 text-sm leading-6 text-slate-300 whitespace-pre-wrap">
                        {detail?.config ? JSON.stringify(detail.config, null, 2) : "-"}
                      </pre>
                    </div>
                  )}
                  {activeTab === "tools" && (
                    <div className="space-y-2">
                      <span className="text-slate-400">工具列表 (default_tools)</span>
                      <ul className="mt-2 flex flex-wrap gap-2">
                        {(detail?.default_tools ?? []).length === 0 ? (
                          <span className="text-slate-500">暂无</span>
                        ) : (
                          (detail?.default_tools ?? []).map((t) => (
                            <li
                              key={t}
                              className="flex items-center gap-1.5 rounded-md border border-slate-700 bg-slate-800/50 px-2.5 py-1 text-xs text-slate-300"
                            >
                              <Wrench className="h-3.5 w-3.5" />
                              {t}
                            </li>
                          ))
                        )}
                      </ul>
                    </div>
                  )}
                  {activeTab === "user" && (
                    <div className="space-y-4 text-sm">
                      <div>
                        <span className="text-slate-400">知识库 (Knowledge Base):</span>{" "}
                        <span className="text-slate-100">{detail?.knowledge_base_name ?? "-"}</span>
                      </div>
                      <div>
                        <span className="text-slate-400">模型 (Model):</span>{" "}
                        <span className="font-mono text-slate-100">{detail?.model ?? "-"}</span>
                      </div>
                      <div>
                        <span className="text-slate-400">工作流 (default_workflows):</span>{" "}
                        <span className="text-slate-100">
                          {(detail?.default_workflows ?? []).join(", ") || "-"}
                        </span>
                      </div>
                    </div>
                  )}
                  {activeTab === "edit" && detail && (
                    <form
                      onSubmit={(e) => {
                        e.preventDefault();
                        handleSaveEdit();
                      }}
                      className="space-y-6"
                    >
                      <div className="space-y-4">
                        <h4 className="text-sm font-medium text-slate-300">身份设定</h4>
                        <div className="space-y-2">
                          <Label>名称 (Name) *</Label>
                          <Input
                            value={editForm.name}
                            onChange={(e) => setEditForm((f) => ({ ...f, name: e.target.value }))}
                            placeholder="智能员工名称"
                            required
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>描述 (Description)</Label>
                          <Textarea
                            value={editForm.description}
                            onChange={(e) => setEditForm((f) => ({ ...f, description: e.target.value }))}
                            placeholder="身份描述"
                            rows={3}
                          />
                        </div>
                        <div className="text-xs text-slate-500">
                          模板 (只读): {detail.template_name ?? "-"}
                        </div>
                      </div>
                      <div className="space-y-4">
                        <h4 className="text-sm font-medium text-slate-300">灵魂核心</h4>
                        <div className="space-y-2">
                          <Label>系统提示词 (System Prompt)</Label>
                          <Textarea
                            value={editForm.system_prompt}
                            onChange={(e) => setEditForm((f) => ({ ...f, system_prompt: e.target.value }))}
                            placeholder="系统提示词…"
                            rows={8}
                            className="font-mono text-sm"
                          />
                        </div>
                      </div>
                      <div className="space-y-4">
                        <h4 className="text-sm font-medium text-slate-300">行为规范 (Config JSON)</h4>
                        <div className="space-y-2">
                          <Label>Config - 存入 agent_instances.config</Label>
                          <Textarea
                            value={editForm.configJson}
                            onChange={(e) => setEditForm((f) => ({ ...f, configJson: e.target.value }))}
                            placeholder='{"behavior": "..."}'
                            rows={6}
                            className="font-mono text-sm"
                          />
                        </div>
                      </div>
                      <div className="space-y-4">
                        <h4 className="text-sm font-medium text-slate-300">用户画像</h4>
                        <div className="space-y-2">
                          <Label>模型 (Model)</Label>
                          <Input
                            value={editForm.model}
                            onChange={(e) => setEditForm((f) => ({ ...f, model: e.target.value }))}
                            placeholder="gpt-4"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>知识库 (Knowledge Base)</Label>
                          <select
                            className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
                            value={editForm.knowledge_base_id}
                            onChange={(e) =>
                              setEditForm((f) => ({ ...f, knowledge_base_id: e.target.value }))
                            }
                          >
                            <option value="">不绑定</option>
                            {kbs.map((kb) => (
                              <option key={kb.id} value={kb.id}>
                                {kb.name}
                              </option>
                            ))}
                          </select>
                        </div>
                      </div>
                      <div className="flex justify-end gap-2 pt-4">
                        <Button
                          type="submit"
                          disabled={updateMutation.isPending}
                        >
                          {updateMutation.isPending ? (
                            <>
                              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              保存中…
                            </>
                          ) : (
                            "保存"
                          )}
                        </Button>
                        {updateMutation.isError && (
                          <span className="text-sm text-red-400">
                            {(updateMutation.error as Error)?.message}
                          </span>
                        )}
                      </div>
                    </form>
                  )}
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </section>

      <Dialog open={showCreateFromTemplate} onOpenChange={setShowCreateFromTemplate}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-sky-400" />
              从模板创建智能员工
            </DialogTitle>
            <DialogDescription>
              选择 Agent 模板与所属项目，即可快速创建智能员工实例。
            </DialogDescription>
          </DialogHeader>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              const pid = templateForm.projectId || defaultProjectId;
              if (!templateForm.templateId || !pid || !templateForm.name.trim()) return;
              createFromTemplateMutation.mutate({
                template_id: templateForm.templateId,
                project_id: pid,
                name: templateForm.name.trim(),
              });
            }}
            className="space-y-4"
          >
            <div className="space-y-2">
              <Label htmlFor="tpl-template">选择模板 *</Label>
              <select
                id="tpl-template"
                className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
                value={templateForm.templateId}
                onChange={(e) => {
                  const t = templates.find((x) => x.id === e.target.value);
                  setTemplateForm((f) => ({
                    ...f,
                    templateId: e.target.value,
                    name: t?.name ?? f.name,
                  }));
                }}
                required
              >
                <option value="">请选择模板</option>
                {templates.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name} ({t.model})
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="tpl-project">所属项目 *</Label>
              <select
                id="tpl-project"
                className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
                value={templateForm.projectId || defaultProjectId}
                onChange={(e) =>
                  setTemplateForm((f) => ({ ...f, projectId: e.target.value }))
                }
                required
              >
                <option value="">请选择项目</option>
                {(projectsQuery.data ?? []).map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="tpl-name">员工名称 *</Label>
              <Input
                id="tpl-name"
                value={templateForm.name}
                onChange={(e) =>
                  setTemplateForm((f) => ({ ...f, name: e.target.value }))
                }
                placeholder="例如：内容运营专员"
                required
              />
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowCreateFromTemplate(false)}
              >
                取消
              </Button>
              <Button
                type="submit"
                disabled={
                  !templateForm.templateId ||
                  !(templateForm.projectId || defaultProjectId) ||
                  !templateForm.name.trim() ||
                  createFromTemplateMutation.isPending
                }
              >
                {createFromTemplateMutation.isPending ? "创建中…" : "创建"}
              </Button>
            </DialogFooter>
            {createFromTemplateMutation.isError && (
              <p className="text-sm text-red-400">
                {(createFromTemplateMutation.error as Error)?.message ?? "创建失败"}
              </p>
            )}
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
