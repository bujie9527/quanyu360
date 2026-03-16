"use client";

import { useQuery } from "@tanstack/react-query";
import { Search, Users } from "lucide-react";
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
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { listAdminTenants, listAdminUsers } from "@/lib/api-admin";

const ALL_TENANTS = "__all__";

export default function UserManagementPage() {
  const [tenantFilter, setTenantFilter] = useState<string>(ALL_TENANTS);
  const [keyword, setKeyword] = useState("");

  const tenantsQuery = useQuery({
    queryKey: ["admin-tenants"],
    queryFn: () => listAdminTenants({ limit: 500 })
  });

  const usersQuery = useQuery({
    queryKey: ["admin-users", tenantFilter],
    queryFn: () =>
      listAdminUsers({
        tenant_id: tenantFilter === ALL_TENANTS ? undefined : tenantFilter,
        limit: 200
      })
  });

  const users = usersQuery.data?.items ?? [];
  const total = usersQuery.data?.total ?? 0;
  const tenants = tenantsQuery.data?.items ?? [];

  const filteredUsers = keyword.trim()
    ? users.filter(
        (u) =>
          u.email.toLowerCase().includes(keyword.toLowerCase()) ||
          (u.full_name ?? "").toLowerCase().includes(keyword.toLowerCase())
      )
    : users;

  return (
    <div className="space-y-6">
      <PageHero
        eyebrow="用户管理"
        title="跨租户查看用户"
        description="浏览和管理所有组织的用户、角色与状态。"
      />

      <section className="grid gap-4 md:grid-cols-3">
        <MetricCard label="用户总数" value={String(total)} icon={Users} />
        <MetricCard
          label="活跃"
          value={String(users.filter((u) => u.status === "active").length)}
        />
        <MetricCard
          label="租户数"
          value={String(tenants.length)}
        />
      </section>

      <FilterBar title="筛选与搜索" description="按租户筛选，按邮箱或姓名搜索。">
        <div className="relative min-w-[260px] flex-1">
          <Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-slate-400" />
          <Input
            className="pl-9"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="搜索邮箱或姓名"
          />
        </div>
        <Select value={tenantFilter} onValueChange={setTenantFilter}>
          <SelectTrigger className="max-w-[220px]">
            <SelectValue placeholder="全部租户" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL_TENANTS}>全部租户</SelectItem>
            {tenants.map((t) => (
              <SelectItem key={t.id} value={t.id}>
                {t.name} ({t.slug})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </FilterBar>

      <TableShell>
        <div className="p-6">
          <PanelHeader
            title="用户列表"
            description="平台上所有已注册用户。"
          />
          {filteredUsers.length === 0 ? (
            <EmptyState
              title="暂无用户"
              description="没有符合筛选条件的用户。"
              icon={Users}
            />
          ) : (
            <DataTable
              headers={["用户", "邮箱", "租户", "角色", "状态", "创建时间"]}
            >
              {filteredUsers.map((u) => {
                const tenant = tenants.find((t) => t.id === u.tenant_id);
                return (
                  <DataRow key={u.id}>
                    <DataCell>
                      <div>
                        <p className="font-medium text-slate-100">{u.full_name || "-"}</p>
                        <p className="text-xs text-slate-400">{u.id}</p>
                      </div>
                    </DataCell>
                    <DataCell>{u.email}</DataCell>
                    <DataCell>
                      <span className="text-slate-300">{tenant?.name ?? tenant?.slug ?? u.tenant_id}</span>
                    </DataCell>
                    <DataCell>
                      <StatusBadge value={u.role} />
                    </DataCell>
                    <DataCell>
                      <StatusBadge value={u.status} />
                    </DataCell>
                    <DataCell className="text-slate-400">
                      {u.created_at
                        ? new Date(u.created_at).toLocaleDateString()
                        : "-"}
                    </DataCell>
                  </DataRow>
                );
              })}
            </DataTable>
          )}
        </div>
      </TableShell>
    </div>
  );
}
