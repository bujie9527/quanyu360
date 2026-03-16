"use client";

import { useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import { zhCN } from "date-fns/locale";
import { ShieldCheck } from "lucide-react";
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
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  listAdminAuditLogs,
  listAdminTenants,
  type AuditLogEntry
} from "@/lib/api-admin";

const ALL_TENANTS = "__all__";
const ALL_ENTITY_TYPES = "__all__";
const ALL_ACTIONS = "__all__";
const ENTITY_TYPES = [
  { value: "agent_run", label: "Agent 执行" },
  { value: "tool_call", label: "工具调用" },
  { value: "workflow_execution", label: "流程执行" }
];
const ACTIONS = [
  { value: "execute", label: "执行" }
];

function PayloadSummary({ payload }: { payload: Record<string, unknown> }) {
  const keys = Object.keys(payload);
  if (keys.length === 0) return <span className="text-slate-500">-</span>;
  const preview =
    "status" in payload
      ? String(payload.status)
      : "tool_name" in payload
        ? `${payload.tool_name}:${payload.action ?? ""}`
        : keys.slice(0, 3).join(", ");
  return (
    <span className="truncate text-sm text-slate-300" title={JSON.stringify(payload)}>
      {preview}
    </span>
  );
}

export default function AuditLogsPage() {
  const [tenantFilter, setTenantFilter] = useState<string>(ALL_TENANTS);
  const [entityTypeFilter, setEntityTypeFilter] = useState<string>(ALL_ENTITY_TYPES);
  const [actionFilter, setActionFilter] = useState<string>(ALL_ACTIONS);
  const [correlationId, setCorrelationId] = useState("");
  const [sinceDate, setSinceDate] = useState("");
  const [untilDate, setUntilDate] = useState("");
  const [page, setPage] = useState(0);
  const limit = 50;

  const tenantsQuery = useQuery({
    queryKey: ["admin-tenants"],
    queryFn: () => listAdminTenants({ limit: 500 })
  });

  const auditQuery = useQuery({
    queryKey: [
      "admin-audit",
      tenantFilter,
      entityTypeFilter,
      actionFilter,
      correlationId,
      sinceDate,
      untilDate,
      page
    ],
    queryFn: () =>
      listAdminAuditLogs({
        tenant_id: tenantFilter === ALL_TENANTS ? undefined : tenantFilter,
        entity_type: entityTypeFilter === ALL_ENTITY_TYPES ? undefined : entityTypeFilter,
        action: actionFilter === ALL_ACTIONS ? undefined : actionFilter,
        correlation_id: correlationId.trim() || undefined,
        since: sinceDate ? `${sinceDate}T00:00:00Z` : undefined,
        until: untilDate ? `${untilDate}T23:59:59Z` : undefined,
        limit,
        offset: page * limit
      })
  });

  const items: AuditLogEntry[] = auditQuery.data?.items ?? [];
  const total = auditQuery.data?.total ?? 0;
  const tenants = tenantsQuery.data?.items ?? [];

  const agentCount = items.filter((i) => i.entity_type === "agent_run").length;
  const toolCount = items.filter((i) => i.entity_type === "tool_call").length;
  const workflowCount = items.filter((i) => i.entity_type === "workflow_execution").length;

  return (
    <div className="space-y-6">
      <PageHero
        eyebrow="审计日志"
        title="AI 行为审计"
        description="查看 Agent 执行、工具调用与流程执行的审计记录。"
      />

      <section className="grid gap-4 md:grid-cols-4">
        <MetricCard
          label="本页 Agent 执行"
          value={String(agentCount)}
          icon={ShieldCheck}
        />
        <MetricCard label="本页 工具调用" value={String(toolCount)} />
        <MetricCard label="本页 流程执行" value={String(workflowCount)} />
        <MetricCard label="总记录数" value={String(total)} />
      </section>

      <FilterBar
        title="筛选"
        description="按租户、类型、关联 ID、时间范围筛选。"
      >
        <Select value={tenantFilter} onValueChange={setTenantFilter}>
          <SelectTrigger className="max-w-[200px]">
            <SelectValue placeholder="租户" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL_TENANTS}>全部租户</SelectItem>
            {tenants.map((t) => (
              <SelectItem key={t.id} value={t.id}>
                {t.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={entityTypeFilter} onValueChange={setEntityTypeFilter}>
          <SelectTrigger className="max-w-[180px]">
            <SelectValue placeholder="类型" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL_ENTITY_TYPES}>全部类型</SelectItem>
            {ENTITY_TYPES.map((e) => (
              <SelectItem key={e.value} value={e.value}>
                {e.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={actionFilter} onValueChange={setActionFilter}>
          <SelectTrigger className="max-w-[120px]">
            <SelectValue placeholder="动作" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL_ACTIONS}>全部</SelectItem>
            {ACTIONS.map((a) => (
              <SelectItem key={a.value} value={a.value}>
                {a.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Input
          className="max-w-[240px]"
          placeholder="关联 ID (task_id, execution_id)"
          value={correlationId}
          onChange={(e) => setCorrelationId(e.target.value)}
        />
        <Input
          type="date"
          className="max-w-[160px]"
          placeholder="开始日期"
          value={sinceDate}
          onChange={(e) => setSinceDate(e.target.value)}
        />
        <Input
          type="date"
          className="max-w-[160px]"
          placeholder="结束日期"
          value={untilDate}
          onChange={(e) => setUntilDate(e.target.value)}
        />
      </FilterBar>

      <TableShell>
        <div className="p-6">
          <PanelHeader
            title="审计记录"
            description="按时间倒序。支持分页。"
          />
          {items.length === 0 ? (
            <EmptyState
              title="暂无审计记录"
              description="筛选条件下暂无记录，或 AI 执行尚未产生审计。"
              icon={ShieldCheck}
            />
          ) : (
            <>
              <DataTable
                headers={["时间", "类型", "动作", "租户", "关联 ID", "详情", "Payload"]}
              >
                {items.map((e) => (
                  <DataRow key={e.id}>
                    <DataCell className="whitespace-nowrap text-slate-400">
                      {e.created_at
                        ? format(new Date(e.created_at), "yyyy-MM-dd HH:mm:ss", {
                            locale: zhCN
                          })
                        : "-"}
                    </DataCell>
                    <DataCell>
                      <Badge
                        variant={
                          e.entity_type === "agent_run"
                            ? "default"
                            : e.entity_type === "tool_call"
                              ? "success"
                              : "outline"
                        }
                        className="font-mono text-xs"
                      >
                        {e.entity_type}
                      </Badge>
                    </DataCell>
                    <DataCell className="text-slate-300">{e.action}</DataCell>
                    <DataCell className="max-w-[100px] truncate text-xs text-slate-500">
                      {tenants.find((t) => t.id === e.tenant_id)?.name ?? e.tenant_id?.slice(0, 8) ?? "-"}
                    </DataCell>
                    <DataCell className="max-w-[180px] truncate font-mono text-xs text-slate-400">
                      {e.correlation_id || "-"}
                    </DataCell>
                    <DataCell>
                      <PayloadSummary payload={e.payload} />
                    </DataCell>
                    <DataCell>
                      <details className="group">
                        <summary className="cursor-pointer text-xs text-slate-500 hover:text-slate-400">
                          展开
                        </summary>
                        <pre className="mt-1 max-h-32 max-w-md overflow-auto rounded bg-slate-900/80 p-2 text-xs text-slate-400">
                          {JSON.stringify(e.payload, null, 2)}
                        </pre>
                      </details>
                    </DataCell>
                  </DataRow>
                ))}
              </DataTable>
              <div className="mt-4 flex items-center justify-between">
                <p className="text-sm text-slate-400">
                  第 {page * limit + 1}–{Math.min((page + 1) * limit, total)} 条，共 {total} 条
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
                    disabled={(page + 1) * limit >= total}
                    onClick={() => setPage((p) => p + 1)}
                  >
                    下一页
                  </Button>
                </div>
              </div>
            </>
          )}
        </div>
      </TableShell>
    </div>
  );
}
