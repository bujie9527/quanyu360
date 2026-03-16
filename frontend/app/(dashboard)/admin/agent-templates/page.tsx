"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronDown, ChevronUp, FileText, Pencil, Plus, Search, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";

import {
  DataCell,
  DataRow,
  DataTable,
  FilterBar,
  MetricCard,
  PageHero,
  PanelHeader,
  TableShell,
} from "@/components/shared/admin-kit";
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
import {
  createAgentTemplate,
  deleteAgentTemplate,
  getAgentTemplate,
  listAgentTemplates,
  updateAgentTemplate,
  type AgentTemplateItem,
} from "@/lib/api-admin";

type TemplateForm = {
  name: string;
  description: string;
  model: string;
  system_prompt: string;
  default_tools: string;
  default_workflows: string;
  enabled: boolean;
};

const emptyForm: TemplateForm = {
  name: "",
  description: "",
  model: "gpt-4",
  system_prompt: "",
  default_tools: "",
  default_workflows: "",
  enabled: true,
};

function toForm(t: AgentTemplateItem | null): TemplateForm {
  if (!t) return emptyForm;
  return {
    name: t.name ?? "",
    description: (t as { description?: string }).description ?? "",
    model: t.model ?? "gpt-4",
    system_prompt: (t as { system_prompt?: string }).system_prompt ?? "",
    default_tools: ((t as { default_tools?: string[] }).default_tools ?? []).join(", "),
    default_workflows: ((t as { default_workflows?: string[] }).default_workflows ?? []).join(", "),
    enabled: (t as { enabled?: boolean }).enabled ?? true,
  };
}

function parseList(s: string): string[] {
  return s
    .split(/[,\s]+/)
    .map((x) => x.trim())
    .filter(Boolean);
}

export default function AdminAgentTemplatesPage() {
  const queryClient = useQueryClient();
  const [keyword, setKeyword] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [form, setForm] = useState<TemplateForm>(emptyForm);

  const templatesQuery = useQuery({
    queryKey: ["admin-agent-templates"],
    queryFn: () => listAgentTemplates({ limit: 200 }),
  });

  const templateDetailQuery = useQuery({
    queryKey: ["admin-agent-template", editId],
    queryFn: () => getAgentTemplate(editId!),
    enabled: !!editId,
  });

  const createMutation = useMutation({
    mutationFn: createAgentTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-agent-templates"] });
      setForm(emptyForm);
      setShowCreate(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Parameters<typeof updateAgentTemplate>[1] }) =>
      updateAgentTemplate(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-agent-templates"] });
      queryClient.invalidateQueries({ queryKey: ["admin-agent-template", editId] });
      setEditId(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteAgentTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-agent-templates"] });
      setEditId(null);
    },
  });

  const templates = (templatesQuery.data?.items ?? []) as AgentTemplateItem[];
  const total = templatesQuery.data?.total ?? templates.length;
  const filtered =
    keyword.trim()
      ? templates.filter(
          (t) =>
            t.name?.toLowerCase().includes(keyword.toLowerCase()) ||
            (t as { description?: string }).description?.toLowerCase().includes(keyword.toLowerCase()) ||
            t.model?.toLowerCase().includes(keyword.toLowerCase())
        )
      : templates;

  const handleOpenEdit = (id: string) => {
    setEditId(id);
    setForm(emptyForm);
  };

  useEffect(() => {
    if (editId && templateDetailQuery.data) {
      setForm(toForm(templateDetailQuery.data as AgentTemplateItem));
    }
  }, [editId, templateDetailQuery.data]);

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) return;
    createMutation.mutate({
      name: form.name.trim(),
      description: form.description.trim() || null,
      model: form.model.trim() || "gpt-4",
      system_prompt: form.system_prompt.trim() || "",
      default_tools: parseList(form.default_tools),
      default_workflows: parseList(form.default_workflows),
      enabled: form.enabled,
    });
  };

  const handleUpdate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!editId || !form.name.trim()) return;
    updateMutation.mutate({
      id: editId,
      payload: {
        name: form.name.trim(),
        description: form.description.trim() || null,
        model: form.model.trim() || "gpt-4",
        system_prompt: form.system_prompt.trim() || "",
        default_tools: parseList(form.default_tools),
        default_workflows: parseList(form.default_workflows),
        enabled: form.enabled,
      },
    });
  };

  const handleDelete = (t: AgentTemplateItem) => {
    if (!confirm(`确定要删除模板「${t.name}」吗？`)) return;
    deleteMutation.mutate(t.id);
  };

  return (
    <div className="space-y-6">
      <PageHero
        eyebrow="AI员工"
        title="Agent Templates"
        description="Agent 模板管理，定义可复用的 Agent 配置。"
      >
        <Button onClick={() => setShowCreate(!showCreate)} className="gap-2">
          <Plus className="h-4 w-4" />
          新建模板
        </Button>
      </PageHero>

      {showCreate && (
        <Card className="border-sky-500/20 bg-sky-500/5">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Plus className="h-5 w-5 text-sky-300" />
                新建 Agent 模板
              </CardTitle>
              <CardDescription>创建可复用的 Agent 配置模板。</CardDescription>
            </div>
            <Button variant="ghost" size="sm" onClick={() => setShowCreate(false)}>
              {showCreate ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </Button>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="create-name">名称 *</Label>
                  <Input
                    id="create-name"
                    placeholder="例如：内容运营 Agent"
                    value={form.name}
                    onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="create-model">模型</Label>
                  <Input
                    id="create-model"
                    placeholder="gpt-4"
                    value={form.model}
                    onChange={(e) => setForm((f) => ({ ...f, model: e.target.value }))}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="create-desc">描述</Label>
                <Input
                  id="create-desc"
                  placeholder="简要描述"
                  value={form.description}
                  onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="create-prompt">System Prompt</Label>
                <Textarea
                  id="create-prompt"
                  placeholder="Agent 系统提示词"
                  value={form.system_prompt}
                  onChange={(e) => setForm((f) => ({ ...f, system_prompt: e.target.value }))}
                  rows={3}
                />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="create-tools">工具（逗号分隔）</Label>
                  <Input
                    id="create-tools"
                    placeholder="server.create, wordpress.install"
                    value={form.default_tools}
                    onChange={(e) => setForm((f) => ({ ...f, default_tools: e.target.value }))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="create-workflows">工作流（逗号分隔）</Label>
                  <Input
                    id="create-workflows"
                    placeholder="workflow-slug-1, workflow-slug-2"
                    value={form.default_workflows}
                    onChange={(e) => setForm((f) => ({ ...f, default_workflows: e.target.value }))}
                  />
                </div>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="create-enabled"
                  checked={form.enabled}
                  onChange={(e) => setForm((f) => ({ ...f, enabled: e.target.checked }))}
                  className="h-4 w-4 rounded border-slate-600 bg-slate-800"
                />
                <Label htmlFor="create-enabled">启用</Label>
              </div>
              <div className="flex gap-3">
                <Button type="submit" disabled={createMutation.isPending}>
                  {createMutation.isPending ? "创建中…" : "创建"}
                </Button>
                <Button type="button" variant="outline" onClick={() => setShowCreate(false)}>
                  取消
                </Button>
              </div>
              {createMutation.isError && (
                <p className="text-sm text-red-400">{(createMutation.error as Error)?.message ?? "创建失败"}</p>
              )}
            </form>
          </CardContent>
        </Card>
      )}

      <section className="grid gap-4 md:grid-cols-2">
        <MetricCard label="模板总数" value={String(total)} icon={FileText} />
      </section>

      <FilterBar title="搜索" description="按名称、描述或模型搜索。">
        <div className="relative min-w-[260px] flex-1">
          <Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-slate-400" />
          <Input
            className="pl-9"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="搜索模板…"
          />
        </div>
      </FilterBar>

      <TableShell>
        <div className="p-6">
          <PanelHeader title="Agent Templates" description="平台上的所有 Agent 模板。" />
          {templatesQuery.isLoading ? (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-12 text-center text-sm text-slate-400">
              加载中…
            </div>
          ) : filtered.length === 0 ? (
            <EmptyState
              title="暂无 Agent 模板"
              description={keyword ? "没有匹配的模板。" : "暂无 Agent 模板。"}
              icon={FileText}
            />
          ) : (
            <DataTable headers={["模板", "描述", "模型", "工具数", "工作流数", "操作"]}>
              {filtered.map((t) => (
                <DataRow key={t.id}>
                  <DataCell>
                    <p className="font-medium text-slate-100">{t.name}</p>
                  </DataCell>
                  <DataCell className="text-slate-400 line-clamp-1 max-w-[200px]">
                    {(t as { description?: string }).description ?? "-"}
                  </DataCell>
                  <DataCell className="font-mono text-slate-400">{t.model ?? "-"}</DataCell>
                  <DataCell className="text-slate-400">
                    {((t as { default_tools?: string[] }).default_tools ?? []).length}
                  </DataCell>
                  <DataCell className="text-slate-400">
                    {((t as { default_workflows?: string[] }).default_workflows ?? []).length}
                  </DataCell>
                  <DataCell>
                    <div className="flex gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="gap-1"
                        onClick={() => handleOpenEdit(t.id)}
                      >
                        <Pencil className="h-3.5 w-3.5" />
                        编辑
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="gap-1 text-red-400 hover:text-red-300 hover:bg-red-500/10"
                        onClick={() => handleDelete(t)}
                        disabled={deleteMutation.isPending}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                        删除
                      </Button>
                    </div>
                  </DataCell>
                </DataRow>
              ))}
            </DataTable>
          )}
        </div>
      </TableShell>

      <Dialog open={!!editId} onOpenChange={(open) => !open && setEditId(null)}>
        <DialogContent className="max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>编辑模板</DialogTitle>
            <DialogDescription>修改 Agent 模板配置。</DialogDescription>
          </DialogHeader>
          {templateDetailQuery.isLoading ? (
            <div className="py-8 text-center text-slate-400">加载中…</div>
          ) : (
            <form onSubmit={handleUpdate} className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="edit-name">名称 *</Label>
                  <Input
                    id="edit-name"
                    value={form.name}
                    onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="edit-model">模型</Label>
                  <Input
                    id="edit-model"
                    value={form.model}
                    onChange={(e) => setForm((f) => ({ ...f, model: e.target.value }))}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-desc">描述</Label>
                <Input
                  id="edit-desc"
                  value={form.description}
                  onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-prompt">System Prompt</Label>
                <Textarea
                  id="edit-prompt"
                  value={form.system_prompt}
                  onChange={(e) => setForm((f) => ({ ...f, system_prompt: e.target.value }))}
                  rows={4}
                />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="edit-tools">工具（逗号分隔）</Label>
                  <Input
                    id="edit-tools"
                    value={form.default_tools}
                    onChange={(e) => setForm((f) => ({ ...f, default_tools: e.target.value }))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="edit-workflows">工作流（逗号分隔）</Label>
                  <Input
                    id="edit-workflows"
                    value={form.default_workflows}
                    onChange={(e) => setForm((f) => ({ ...f, default_workflows: e.target.value }))}
                  />
                </div>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="edit-enabled"
                  checked={form.enabled}
                  onChange={(e) => setForm((f) => ({ ...f, enabled: e.target.checked }))}
                  className="h-4 w-4 rounded border-slate-600 bg-slate-800"
                />
                <Label htmlFor="edit-enabled">启用</Label>
              </div>
              <DialogFooter>
                <Button type="submit" disabled={updateMutation.isPending}>
                  {updateMutation.isPending ? "保存中…" : "保存"}
                </Button>
                <Button type="button" variant="outline" onClick={() => setEditId(null)}>
                  取消
                </Button>
              </DialogFooter>
              {updateMutation.isError && (
                <p className="text-sm text-red-400">
                  {(updateMutation.error as Error)?.message ?? "保存失败"}
                </p>
              )}
            </form>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
