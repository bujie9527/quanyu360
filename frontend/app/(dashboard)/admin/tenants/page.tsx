"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BriefcaseBusiness, ChevronDown, ChevronUp, Plus, Search } from "lucide-react";
import { useState } from "react";

import {
  DataCell,
  DataRow,
  DataTable,
  FilterBar,
  MetricCard,
  PageHero,
  PanelHeader,
  TableShell
} from "@/components/shared/admin-kit";
import { EmptyState } from "@/components/shared/empty-state";
import { StatusBadge } from "@/components/shared/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { createTenant, getTenantDetail, listAdminTenants } from "@/lib/api-admin";

export default function TenantManagementPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [formName, setFormName] = useState("");
  const [formSlug, setFormSlug] = useState("");
  const [detailTenantId, setDetailTenantId] = useState<string | null>(null);

  const tenantsQuery = useQuery({
    queryKey: ["admin-tenants"],
    queryFn: () => listAdminTenants({ limit: 200 })
  });

  const tenantDetailQuery = useQuery({
    queryKey: ["admin-tenant-detail", detailTenantId],
    queryFn: () => getTenantDetail(detailTenantId!),
    enabled: !!detailTenantId
  });

  const createMutation = useMutation({
    mutationFn: createTenant,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-tenants"] });
      setFormName("");
      setFormSlug("");
      setShowCreate(false);
    }
  });

  const tenants = tenantsQuery.data?.items ?? [];
  const total = tenantsQuery.data?.total ?? 0;
  const filtered = search.trim()
    ? tenants.filter(
        (t) =>
          t.name.toLowerCase().includes(search.toLowerCase()) ||
          t.slug.toLowerCase().includes(search.toLowerCase())
      )
    : tenants;

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formName.trim() || !formSlug.trim()) return;
    createMutation.mutate({
      name: formName.trim(),
      slug: formSlug.trim().toLowerCase().replace(/\s+/g, "-")
    });
  };

  const handleSlugFromName = () => {
    const slug = formName
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "");
    setFormSlug(slug);
  };

  return (
    <div className="space-y-6">
      <PageHero
        eyebrow="租户管理"
        title="查看与创建租户"
        description="管理平台组织。每个租户拥有独立的用户、项目和资源。"
      >
        <Button onClick={() => setShowCreate(!showCreate)} className="gap-2">
          <Plus className="h-4 w-4" />
          创建租户
        </Button>
      </PageHero>

      {showCreate && (
        <Card className="border-sky-500/20 bg-sky-500/5">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Plus className="h-5 w-5 text-sky-300" />
                创建新租户
              </CardTitle>
              <CardDescription>向平台添加新组织。</CardDescription>
            </div>
            <Button variant="ghost" size="sm" onClick={() => setShowCreate(false)}>
              {showCreate ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </Button>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="tenant-name">名称</Label>
                  <Input
                    id="tenant-name"
                    placeholder="示例企业"
                    value={formName}
                    onChange={(e) => setFormName(e.target.value)}
                    onBlur={handleSlugFromName}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="tenant-slug">标识</Label>
                  <Input
                    id="tenant-slug"
                    placeholder="demo-enterprise"
                    value={formSlug}
                    onChange={(e) => setFormSlug(e.target.value)}
                    className="font-mono"
                    required
                  />
                  <p className="text-xs text-slate-500">唯一标识符，如 demo-enterprise</p>
                </div>
              </div>
              <div className="flex gap-3">
                <Button type="submit" disabled={createMutation.isPending}>
                  {createMutation.isPending ? "创建中…" : "创建租户"}
                </Button>
                <Button type="button" variant="outline" onClick={() => setShowCreate(false)}>
                  取消
                </Button>
              </div>
              {createMutation.isError && (
                <p className="text-sm text-red-400">
                  {(createMutation.error as Error)?.message ?? "创建租户失败，请重试。"}
                </p>
              )}
            </form>
          </CardContent>
        </Card>
      )}

      <section className="grid gap-4 md:grid-cols-3">
        <MetricCard label="租户总数" value={String(total)} icon={BriefcaseBusiness} />
        <MetricCard label="活跃" value={String(tenants.filter((t) => t.status === "active").length)} />
        <MetricCard label="草稿/归档" value={String(tenants.filter((t) => t.status !== "active").length)} />
      </section>

      <FilterBar title="搜索" description="按名称或标识搜索租户。">
        <div className="relative min-w-[260px] flex-1">
          <Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-slate-400" />
          <Input
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="搜索租户…"
          />
        </div>
      </FilterBar>

      <TableShell>
        <div className="p-6">
          <PanelHeader
            title="租户列表"
            description="平台上的所有组织。"
          />
          {filtered.length === 0 ? (
            <EmptyState
              title="暂无租户"
              description={search ? "没有匹配的租户。" : "创建第一个租户以开始使用。"}
              icon={BriefcaseBusiness}
            />
          ) : (
            <>
            <DataTable headers={["名称", "标识", "状态", "方案", "创建时间", "操作"]}>
              {filtered.map((t) => (
                <DataRow
                  key={t.id}
                  selected={detailTenantId === t.id}
                  onClick={() => setDetailTenantId(detailTenantId === t.id ? null : t.id)}
                >
                  <DataCell>
                    <div>
                      <p className="font-medium text-slate-100">{t.name}</p>
                      <p className="text-xs text-slate-500">{t.id}</p>
                    </div>
                  </DataCell>
                  <DataCell className="font-mono text-slate-300">{t.slug}</DataCell>
                  <DataCell>
                    <StatusBadge value={t.status} />
                  </DataCell>
                  <DataCell className="text-slate-300">{t.plan_name}</DataCell>
                  <DataCell className="text-slate-400">
                    {t.created_at ? new Date(t.created_at).toLocaleDateString() : "-"}
                  </DataCell>
                  <DataCell>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        setDetailTenantId(detailTenantId === t.id ? null : t.id);
                      }}
                    >
                      {detailTenantId === t.id ? "收起" : "详情"}
                    </Button>
                  </DataCell>
                </DataRow>
              ))}
            </DataTable>
            {detailTenantId && tenantDetailQuery.data && (
              <div className="mt-4 rounded-xl border border-sky-500/20 bg-sky-500/5 p-4">
                <p className="mb-2 text-sm font-medium text-slate-200">租户详情 · {tenantDetailQuery.data.name}</p>
                <pre className="max-h-48 overflow-auto rounded bg-slate-900/80 p-3 text-xs text-slate-400">
                  {JSON.stringify(
                    {
                      id: tenantDetailQuery.data.id,
                      name: tenantDetailQuery.data.name,
                      slug: tenantDetailQuery.data.slug,
                      status: tenantDetailQuery.data.status,
                      plan_name: tenantDetailQuery.data.plan_name,
                      settings: tenantDetailQuery.data.settings
                    },
                    null,
                    2
                  )}
                </pre>
              </div>
            )}
            </>
          )}
        </div>
      </TableShell>
    </div>
  );
}
