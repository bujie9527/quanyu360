"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronDown, ChevronUp, Loader2, Plus, Shield } from "lucide-react";
import { useState } from "react";

import {
  DataCell,
  DataRow,
  DataTable,
  MetricCard,
  PageHero,
  PanelHeader,
  TableShell
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
  DialogTitle
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  createAdminRole,
  deleteAdminRole,
  listAdminRoles,
  updateAdminRole,
  type RoleSummary
} from "@/lib/api-admin";

export default function RoleManagementPage() {
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [editingRole, setEditingRole] = useState<RoleSummary | null>(null);
  const [deletingRole, setDeletingRole] = useState<RoleSummary | null>(null);
  const [formSlug, setFormSlug] = useState("");
  const [formName, setFormName] = useState("");
  const [formDesc, setFormDesc] = useState("");

  const rolesQuery = useQuery({
    queryKey: ["admin-roles"],
    queryFn: () => listAdminRoles({ limit: 200 })
  });

  const createMutation = useMutation({
    mutationFn: createAdminRole,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-roles"] });
      setFormSlug("");
      setFormName("");
      setFormDesc("");
      setShowCreate(false);
    }
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, ...payload }: { id: string } & Parameters<typeof updateAdminRole>[1]) =>
      updateAdminRole(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-roles"] });
      setEditingRole(null);
    }
  });

  const deleteMutation = useMutation({
    mutationFn: deleteAdminRole,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-roles"] });
      setDeletingRole(null);
    }
  });

  const roles = rolesQuery.data?.items ?? [];
  const total = rolesQuery.data?.total ?? 0;

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formSlug.trim() || !formName.trim()) return;
    createMutation.mutate({
      slug: formSlug.trim().toLowerCase().replace(/\s+/g, "_"),
      name: formName.trim(),
      description: formDesc.trim() || null
    });
  };

  const handleUpdate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingRole) return;
    updateMutation.mutate({
      id: editingRole.id,
      slug: formSlug.trim() || undefined,
      name: formName.trim() || undefined,
      description: formDesc.trim() || null
    });
  };

  const openEdit = (r: RoleSummary) => {
    setEditingRole(r);
    setFormSlug(r.slug);
    setFormName(r.name);
    setFormDesc(r.description ?? "");
  };

  return (
    <div className="space-y-6">
      <PageHero
        eyebrow="角色管理"
        title="RBAC 角色"
        description="创建与管理平台角色，用于 RBAC 权限控制。"
      >
        <Button onClick={() => setShowCreate(!showCreate)} className="gap-2">
          <Plus className="h-4 w-4" />
          创建角色
        </Button>
      </PageHero>

      {showCreate && (
        <Card className="border-sky-500/20 bg-sky-500/5">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Plus className="h-5 w-5 text-sky-300" />
                创建新角色
              </CardTitle>
              <CardDescription>添加平台角色。</CardDescription>
            </div>
            <Button variant="ghost" size="sm" onClick={() => setShowCreate(false)}>
              <ChevronUp className="h-4 w-4" />
            </Button>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="role-slug">标识 (slug)</Label>
                  <Input
                    id="role-slug"
                    placeholder="platform_admin"
                    value={formSlug}
                    onChange={(e) => setFormSlug(e.target.value)}
                    className="font-mono"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="role-name">显示名称</Label>
                  <Input
                    id="role-name"
                    placeholder="平台管理员"
                    value={formName}
                    onChange={(e) => setFormName(e.target.value)}
                    required
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="role-desc">描述（可选）</Label>
                <Input
                  id="role-desc"
                  placeholder="平台级管理权限"
                  value={formDesc}
                  onChange={(e) => setFormDesc(e.target.value)}
                />
              </div>
              <div className="flex gap-3">
                <Button type="submit" disabled={createMutation.isPending}>
                  {createMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  创建
                </Button>
                <Button type="button" variant="outline" onClick={() => setShowCreate(false)}>
                  取消
                </Button>
              </div>
              {createMutation.isError && (
                <p className="text-sm text-red-400">
                  {(createMutation.error as Error)?.message ?? "创建失败"}
                </p>
              )}
            </form>
          </CardContent>
        </Card>
      )}

      <section className="grid gap-4 md:grid-cols-3">
        <MetricCard label="角色总数" value={String(total)} icon={Shield} />
      </section>

      <TableShell>
        <div className="p-6">
          <PanelHeader
            title="角色列表"
            description="平台 RBAC 角色。可在用户管理中将角色分配给用户。"
          />
          {roles.length === 0 ? (
            <EmptyState
              title="暂无角色"
              description="创建第一个角色以开始使用 RBAC。"
              icon={Shield}
            />
          ) : (
            <DataTable headers={["标识", "名称", "描述", "创建时间", "操作"]}>
              {roles.map((r) => (
                <DataRow key={r.id}>
                  <DataCell className="font-mono text-slate-300">{r.slug}</DataCell>
                  <DataCell className="font-medium text-slate-100">{r.name}</DataCell>
                  <DataCell className="max-w-[200px] truncate text-sm text-slate-500">
                    {r.description ?? "—"}
                  </DataCell>
                  <DataCell className="text-slate-400">
                    {r.created_at ? new Date(r.created_at).toLocaleDateString() : "-"}
                  </DataCell>
                  <DataCell>
                    <div className="flex gap-2">
                      <Button variant="ghost" size="sm" onClick={() => openEdit(r)}>
                        编辑
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-red-400 hover:text-red-300"
                        onClick={() => setDeletingRole(r)}
                      >
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

      {/* Edit Dialog */}
      <Dialog open={!!editingRole} onOpenChange={(v) => !v && setEditingRole(null)}>
        <DialogContent>
          <form onSubmit={handleUpdate}>
            <DialogHeader>
              <DialogTitle>编辑角色</DialogTitle>
              <DialogDescription>修改角色信息。</DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="space-y-2">
                <Label>标识 (slug)</Label>
                <Input
                  value={formSlug}
                  onChange={(e) => setFormSlug(e.target.value)}
                  placeholder="platform_admin"
                  className="font-mono"
                />
              </div>
              <div className="space-y-2">
                <Label>显示名称</Label>
                <Input
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  placeholder="平台管理员"
                />
              </div>
              <div className="space-y-2">
                <Label>描述（可选）</Label>
                <Input
                  value={formDesc}
                  onChange={(e) => setFormDesc(e.target.value)}
                  placeholder="描述"
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setEditingRole(null)}>
                取消
              </Button>
              <Button type="submit" disabled={updateMutation.isPending}>
                {updateMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                保存
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirm */}
      <Dialog open={!!deletingRole} onOpenChange={(v) => !v && setDeletingRole(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认删除</DialogTitle>
            <DialogDescription>
              确定要删除角色「{deletingRole?.name}」吗？此操作不可恢复。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeletingRole(null)}>
              取消
            </Button>
            <Button
              variant="outline"
              className="border-red-500/50 text-red-400 hover:bg-red-500/10 hover:text-red-300"
              onClick={() => deletingRole && deleteMutation.mutate(deletingRole.id)}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              删除
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
