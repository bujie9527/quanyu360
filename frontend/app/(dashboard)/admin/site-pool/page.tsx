"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link2, Loader2 } from "lucide-react";
import { useMemo, useState } from "react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  assignSiteToTenant,
  listAdminProjects,
  listAdminTenants,
  listSitePoolSites,
  type SitePoolSiteItem,
} from "@/lib/api-admin";

export default function AdminSitePoolPage() {
  const queryClient = useQueryClient();
  const [assignedFilter, setAssignedFilter] = useState<string>("all");
  const [selectedSiteId, setSelectedSiteId] = useState<string>("");
  const [tenantId, setTenantId] = useState<string>("");
  const [projectId, setProjectId] = useState<string>("");

  const sitesQuery = useQuery({
    queryKey: ["admin-site-pool", assignedFilter],
    queryFn: () =>
      listSitePoolSites({
        assigned: assignedFilter === "all" ? undefined : assignedFilter === "assigned",
        limit: 200,
      }),
    refetchInterval: 5000,
  });

  const tenantsQuery = useQuery({ queryKey: ["admin-tenants-lite"], queryFn: () => listAdminTenants({ limit: 500 }) });
  const projectsQuery = useQuery({ queryKey: ["admin-projects-lite"], queryFn: () => listAdminProjects({ limit: 500 }) });

  const selectedSite = useMemo(
    () => (sitesQuery.data?.items ?? []).find((s) => s.id === selectedSiteId) ?? null,
    [sitesQuery.data, selectedSiteId]
  );

  const projectOptions = useMemo(() => {
    const rows = (projectsQuery.data?.items ?? []) as Array<Record<string, unknown>>;
    if (!tenantId) return rows;
    return rows.filter((p) => String(p.tenant_id ?? "") === tenantId);
  }, [projectsQuery.data, tenantId]);

  const assignMutation = useMutation({
    mutationFn: ({ siteId, tId, pId }: { siteId: string; tId: string; pId: string }) =>
      assignSiteToTenant(siteId, { tenant_id: tId, project_id: pId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-site-pool"] });
      setTenantId("");
      setProjectId("");
    },
  });

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm text-slate-400">Admin / 建站中心</p>
        <h1 className="text-2xl font-semibold text-slate-100">站点库</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>站点池列表</CardTitle>
          <CardDescription>查看预建站点，授权给租户后绑定矩阵项目。</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-3 text-sm">
            <label>筛选:</label>
            <select className="rounded border border-slate-700 bg-slate-900 px-2 py-1" value={assignedFilter} onChange={(e) => setAssignedFilter(e.target.value)}>
              <option value="all">全部</option>
              <option value="unassigned">未授权</option>
              <option value="assigned">已授权</option>
            </select>
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            {(sitesQuery.data?.items ?? []).map((site: SitePoolSiteItem) => (
              <button
                key={site.id}
                className={`rounded border p-3 text-left ${selectedSiteId === site.id ? "border-emerald-500 bg-slate-800" : "border-slate-700 bg-slate-900"}`}
                onClick={() => setSelectedSiteId(site.id)}
              >
                <p className="text-sm font-medium text-slate-100">{site.domain}</p>
                <p className="text-xs text-slate-400">{site.pool_status} · server: {site.server_id ?? "-"}</p>
                <p className="text-xs text-slate-500">tenant: {site.tenant_id ?? "-"} · project: {site.project_id ?? "-"}</p>
              </button>
            ))}
            {(sitesQuery.data?.items ?? []).length === 0 && <p className="text-sm text-slate-500">站点池为空</p>}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Link2 className="h-5 w-5" />
            授权与绑定
          </CardTitle>
          <CardDescription>将站点授权给租户并绑定到租户项目。</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-3">
          <div>
            <label className="text-sm">站点</label>
            <select className="mt-2 w-full rounded border border-slate-700 bg-slate-900 px-3 py-2" value={selectedSiteId} onChange={(e) => setSelectedSiteId(e.target.value)}>
              <option value="">选择站点</option>
              {(sitesQuery.data?.items ?? []).filter((x) => !x.tenant_id || !x.project_id).map((site) => (
                <option key={site.id} value={site.id}>{site.domain}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-sm">租户</label>
            <select className="mt-2 w-full rounded border border-slate-700 bg-slate-900 px-3 py-2" value={tenantId} onChange={(e) => setTenantId(e.target.value)}>
              <option value="">选择租户</option>
              {(tenantsQuery.data?.items ?? []).map((t) => (
                <option key={t.id} value={t.id}>{t.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-sm">项目</label>
            <select className="mt-2 w-full rounded border border-slate-700 bg-slate-900 px-3 py-2" value={projectId} onChange={(e) => setProjectId(e.target.value)}>
              <option value="">选择项目</option>
              {projectOptions.map((p) => (
                <option key={String(p.id)} value={String(p.id)}>{String(p.name ?? p.key ?? p.id)}</option>
              ))}
            </select>
          </div>

          <div className="md:col-span-3">
            <button
              className="inline-flex items-center rounded bg-emerald-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
              disabled={!selectedSiteId || !tenantId || !projectId || assignMutation.isPending}
              onClick={() => assignMutation.mutate({ siteId: selectedSiteId, tId: tenantId, pId: projectId })}
            >
              {assignMutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              确认授权并绑定
            </button>
          </div>

          {selectedSite && (
            <p className="md:col-span-3 text-xs text-slate-400">
              当前站点：{selectedSite.domain} · 状态 {selectedSite.pool_status}/{selectedSite.status}
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
