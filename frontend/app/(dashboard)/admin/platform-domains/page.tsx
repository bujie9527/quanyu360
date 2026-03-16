"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Globe, Loader2, Pencil, Plus, Trash2 } from "lucide-react";
import { useState } from "react";

import {
  DataCell,
  DataRow,
  DataTable,
  FilterBar,
  PageHero,
  PanelHeader,
  TableShell
} from "@/components/shared/admin-kit";
import { EmptyState } from "@/components/shared/empty-state";
import { Badge } from "@/components/ui/badge";
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
  createPlatformDomain,
  deletePlatformDomain,
  listServers,
  listPlatformDomains,
  type PlatformDomainItem,
  updatePlatformDomain
} from "@/lib/api-admin";
import { format } from "date-fns";
import { zhCN } from "date-fns/locale";

const STATUS_OPTIONS = [
  { value: "", label: "全部状态" },
  { value: "available", label: "可用" },
  { value: "assigned", label: "已分配" },
  { value: "inactive", label: "停用" }
];

export default function PlatformDomainsPage() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [page, setPage] = useState(0);
  const [createOpen, setCreateOpen] = useState(false);
  const [editItem, setEditItem] = useState<PlatformDomainItem | null>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null);

  const [createForm, setCreateForm] = useState({
    domain: "",
    api_base_url: "",
    server_id: "",
    ssl_enabled: true,
    status: "available"
  });
  const [editForm, setEditForm] = useState({
    domain: "",
    api_base_url: "",
    server_id: "",
    ssl_enabled: true,
    status: "available"
  });

  const domainsQuery = useQuery({
    queryKey: ["admin-platform-domains", statusFilter, page],
    queryFn: () =>
      listPlatformDomains({
        status: statusFilter || undefined,
        limit: 50,
        offset: page * 50
      })
  });
  const serversQuery = useQuery({
    queryKey: ["admin-servers-for-domains"],
    queryFn: () => listServers({ limit: 200 }),
  });

  const createMutation = useMutation({
    mutationFn: createPlatformDomain,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-platform-domains"] });
      setCreateOpen(false);
      setCreateForm({ domain: "", api_base_url: "", server_id: "", ssl_enabled: true, status: "available" });
    }
  });

  const updateMutation = useMutation({
    mutationFn: ({
      id,
      payload
    }: {
      id: string;
      payload: { domain?: string; api_base_url?: string; server_id?: string | null; ssl_enabled?: boolean; status?: string };
    }) => updatePlatformDomain(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-platform-domains"] });
      setEditItem(null);
    }
  });

  const deleteMutation = useMutation({
    mutationFn: deletePlatformDomain,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-platform-domains"] });
      setDeleteId(null);
    }
  });

  const items = domainsQuery.data?.items ?? [];
  const total = domainsQuery.data?.total ?? 0;

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!createForm.domain.trim() || !createForm.api_base_url.trim()) return;
    createMutation.mutate({
      domain: createForm.domain.trim(),
      api_base_url: createForm.api_base_url.trim(),
      server_id: createForm.server_id || null,
      ssl_enabled: createForm.ssl_enabled,
      status: createForm.status
    });
  };

  const handleEdit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!editItem) return;
    const payload: { domain?: string; api_base_url?: string; server_id?: string | null; ssl_enabled?: boolean; status?: string } = {};
    if (editForm.domain.trim()) payload.domain = editForm.domain.trim();
    if (editForm.api_base_url.trim()) payload.api_base_url = editForm.api_base_url.trim();
    payload.server_id = editForm.server_id || null;
    payload.ssl_enabled = editForm.ssl_enabled;
    payload.status = editForm.status;
    updateMutation.mutate({ id: editItem.id, payload });
  };

  const handleOpenEdit = (item: PlatformDomainItem) => {
    setEditItem(item);
    setEditForm({
      domain: item.domain,
      api_base_url: item.api_base_url,
      server_id: item.server_id ?? "",
      ssl_enabled: item.ssl_enabled,
      status: item.status
    });
  };

  const statusBadgeVariant = (status: string): "default" | "success" | "warning" | "outline" => {
    switch (status) {
      case "available":
        return "success";
      case "assigned":
        return "default";
      case "inactive":
        return "outline";
      default:
        return "outline";
    }
  };

  return (
    <div className="space-y-6">
      <PageHero
        eyebrow="域名管理"
        title="平台域名库"
        description="管理 WordPress 建站可用的域名池，支持新建、编辑与删除。"
      >
        <Button onClick={() => setCreateOpen(true)} className="gap-2">
          <Plus className="h-4 w-4" />
          新建域名
        </Button>
      </PageHero>

      <FilterBar title="筛选" description="按状态筛选域名。">
        <select
          className="max-w-[180px] rounded-xl border border-slate-800 bg-slate-900/60 px-3 py-2 text-sm text-slate-100"
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setPage(0);
          }}
        >
          {STATUS_OPTIONS.map((o) => (
            <option key={o.value || "_all"} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </FilterBar>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="h-5 w-5 text-sky-400" />
            域名列表
          </CardTitle>
          <CardDescription>共 {total} 条记录</CardDescription>
        </CardHeader>
        <CardContent>
          {domainsQuery.isLoading ? (
            <div className="flex justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-sky-400" />
            </div>
          ) : items.length === 0 ? (
            <EmptyState
              title="暂无域名"
              description={statusFilter ? "该状态下无域名记录。" : "新建第一个域名以开始使用。"}
              icon={Globe}
            />
          ) : (
            <>
              <TableShell>
                <DataTable
                  headers={["域名", "API Base URL", "SSL", "状态", "创建时间", "操作"]}
                >
                  {items.map((d) => (
                    <DataRow key={d.id}>
                      <DataCell className="font-mono text-slate-100">{d.domain}</DataCell>
                      <DataCell className="max-w-[240px] truncate text-slate-400">
                        {d.api_base_url}
                      </DataCell>
                      <DataCell>
                        {d.ssl_enabled ? (
                          <Badge variant="outline" className="text-emerald-400">
                            是
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="text-amber-400">
                            否
                          </Badge>
                        )}
                      </DataCell>
                      <DataCell>
                        <Badge variant={statusBadgeVariant(d.status)}>
                          {d.status === "available" ? "可用" : d.status === "assigned" ? "已分配" : "停用"}
                        </Badge>
                      </DataCell>
                      <DataCell className="text-slate-400">
                        {d.created_at
                          ? format(new Date(d.created_at), "yyyy-MM-dd HH:mm", { locale: zhCN })
                          : "-"}
                      </DataCell>
                      <DataCell>
                        <div className="flex gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleOpenEdit(d)}
                            className="gap-1"
                          >
                            <Pencil className="h-4 w-4" />
                            编辑
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setDeleteId(d.id)}
                            className="gap-1 text-red-400 hover:text-red-300 hover:bg-red-500/10"
                          >
                            <Trash2 className="h-4 w-4" />
                            删除
                          </Button>
                        </div>
                      </DataCell>
                    </DataRow>
                  ))}
                </DataTable>
              </TableShell>
              {total > 50 && (
                <div className="mt-4 flex items-center justify-between">
                  <p className="text-sm text-slate-400">
                    第 {page * 50 + 1}–{Math.min((page + 1) * 50, total)} 条，共 {total} 条
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={page === 0}
                      onClick={() => setPage((p) => Math.max(0, p - 1))}
                    >
                      上一页
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={(page + 1) * 50 >= total}
                      onClick={() => setPage((p) => p + 1)}
                    >
                      下一页
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* 新建 Dialog */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <form onSubmit={handleCreate}>
            <DialogHeader>
              <DialogTitle>新建域名</DialogTitle>
              <DialogDescription>添加建站可用的域名及对应 API 配置。</DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="create-domain">域名</Label>
                <Input
                  id="create-domain"
                  placeholder="example.com"
                  value={createForm.domain}
                  onChange={(e) => setCreateForm((f) => ({ ...f, domain: e.target.value }))}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="create-api-base">API Base URL</Label>
                <Input
                  id="create-api-base"
                  placeholder="https://api.example.com"
                  value={createForm.api_base_url}
                  onChange={(e) => setCreateForm((f) => ({ ...f, api_base_url: e.target.value }))}
                  required
                />
              </div>
              <div className="flex items-center justify-between rounded-lg border border-slate-800 p-4">
                <Label htmlFor="create-ssl">启用 SSL</Label>
                <input
                  id="create-ssl"
                  type="checkbox"
                  checked={createForm.ssl_enabled}
                  onChange={(e) => setCreateForm((f) => ({ ...f, ssl_enabled: e.target.checked }))}
                  className="h-4 w-4 rounded border-slate-600 bg-slate-800 text-sky-500 focus:ring-sky-500"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="create-server">关联服务器</Label>
                <select
                  id="create-server"
                  className="w-full rounded-lg border border-slate-800 bg-slate-900/60 px-3 py-2 text-sm text-slate-100"
                  value={createForm.server_id}
                  onChange={(e) => setCreateForm((f) => ({ ...f, server_id: e.target.value }))}
                >
                  <option value="">未关联</option>
                  {(serversQuery.data?.items ?? []).map((s) => (
                    <option key={s.id} value={s.id}>{s.name} ({s.host})</option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="create-status">状态</Label>
                <select
                  id="create-status"
                  className="w-full rounded-lg border border-slate-800 bg-slate-900/60 px-3 py-2 text-sm text-slate-100"
                  value={createForm.status}
                  onChange={(e) => setCreateForm((f) => ({ ...f, status: e.target.value }))}
                >
                  <option value="available">可用</option>
                  <option value="assigned">已分配</option>
                  <option value="inactive">停用</option>
                </select>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setCreateOpen(false)}>
                取消
              </Button>
              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                创建
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* 编辑 Dialog */}
      <Dialog open={!!editItem} onOpenChange={(open) => !open && setEditItem(null)}>
        <DialogContent>
          <form onSubmit={handleEdit}>
            <DialogHeader>
              <DialogTitle>编辑域名</DialogTitle>
              <DialogDescription>{editItem?.domain}</DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="edit-domain">域名</Label>
                <Input
                  id="edit-domain"
                  value={editForm.domain}
                  onChange={(e) => setEditForm((f) => ({ ...f, domain: e.target.value }))}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-api-base">API Base URL</Label>
                <Input
                  id="edit-api-base"
                  value={editForm.api_base_url}
                  onChange={(e) => setEditForm((f) => ({ ...f, api_base_url: e.target.value }))}
                  required
                />
              </div>
              <div className="flex items-center justify-between rounded-lg border border-slate-800 p-4">
                <Label htmlFor="edit-ssl">启用 SSL</Label>
                <input
                  id="edit-ssl"
                  type="checkbox"
                  checked={editForm.ssl_enabled}
                  onChange={(e) => setEditForm((f) => ({ ...f, ssl_enabled: e.target.checked }))}
                  className="h-4 w-4 rounded border-slate-600 bg-slate-800 text-sky-500 focus:ring-sky-500"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-server">关联服务器</Label>
                <select
                  id="edit-server"
                  className="w-full rounded-lg border border-slate-800 bg-slate-900/60 px-3 py-2 text-sm text-slate-100"
                  value={editForm.server_id}
                  onChange={(e) => setEditForm((f) => ({ ...f, server_id: e.target.value }))}
                >
                  <option value="">未关联</option>
                  {(serversQuery.data?.items ?? []).map((s) => (
                    <option key={s.id} value={s.id}>{s.name} ({s.host})</option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-status">状态</Label>
                <select
                  id="edit-status"
                  className="w-full rounded-lg border border-slate-800 bg-slate-900/60 px-3 py-2 text-sm text-slate-100"
                  value={editForm.status}
                  onChange={(e) => setEditForm((f) => ({ ...f, status: e.target.value }))}
                >
                  <option value="available">可用</option>
                  <option value="assigned">已分配</option>
                  <option value="inactive">停用</option>
                </select>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setEditItem(null)}>
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

      {/* 删除确认 Dialog */}
      <Dialog open={!!deleteId} onOpenChange={(open) => !open && setDeleteId(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认删除</DialogTitle>
            <DialogDescription>
              删除后该域名将无法恢复。确认要删除吗？
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteId(null)}>
              取消
            </Button>
            <Button
              variant="outline"
              className="border-red-500/50 text-red-400 hover:bg-red-500/10 hover:text-red-300"
              onClick={() => deleteId && deleteMutation.mutate(deleteId)}
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
