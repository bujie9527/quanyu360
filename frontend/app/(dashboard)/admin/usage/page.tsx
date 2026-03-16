"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BarChart3, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

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
  getQuotas,
  getUsageSummary,
  listAdminTenants,
  listUsageLogs,
  updateTenantQuotas,
  type QuotaList,
  type UsageSummary
} from "@/lib/api-admin";
import { format } from "date-fns";
import { zhCN } from "date-fns/locale";

const USAGE_TYPES = [
  { value: "llm_tokens", label: "LLM Tokens" },
  { value: "workflow_run", label: "流程执行" },
  { value: "tool_execution", label: "工具调用" }
];

export default function UsageAndQuotasPage() {
  const queryClient = useQueryClient();
  const [tenantId, setTenantId] = useState<string>("");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [usageTypeFilter, setUsageTypeFilter] = useState<string>("");
  const [logsPage, setLogsPage] = useState(0);
  const [quotaTenantId, setQuotaTenantId] = useState<string>("");
  const [quotaDialogOpen, setQuotaDialogOpen] = useState(false);
  const [quotaForm, setQuotaForm] = useState({
    tasks_per_month: "",
    llm_requests_per_month: "",
    workflows_per_month: "",
    wordpress_sites_per_month: ""
  });

  const tenantsQuery = useQuery({
    queryKey: ["admin-tenants"],
    queryFn: () => listAdminTenants({ limit: 500 })
  });

  const summaryQuery = useQuery({
    queryKey: ["admin-usage-summary", tenantId, fromDate, toDate],
    queryFn: () =>
      getUsageSummary({
        tenant_id: tenantId,
        from_at: fromDate ? `${fromDate}T00:00:00` : undefined,
        to_at: toDate ? `${toDate}T23:59:59` : undefined
      }),
    enabled: !!tenantId
  });

  const logsQuery = useQuery({
    queryKey: ["admin-usage-logs", tenantId, fromDate, toDate, usageTypeFilter, logsPage],
    queryFn: () =>
      listUsageLogs({
        tenant_id: tenantId || undefined,
        from_at: fromDate ? `${fromDate}T00:00:00` : undefined,
        to_at: toDate ? `${toDate}T23:59:59` : undefined,
        usage_type: usageTypeFilter || undefined,
        limit: 50,
        offset: logsPage * 50
      })
  });

  const quotasQuery = useQuery({
    queryKey: ["admin-quotas", quotaTenantId],
    queryFn: () => getQuotas(quotaTenantId),
    enabled: !!quotaTenantId
  });

  const updateQuotaMutation = useMutation({
    mutationFn: (payload: {
      tasks_per_month?: number;
      llm_requests_per_month?: number;
      workflows_per_month?: number;
      wordpress_sites_per_month?: number;
    }) => updateTenantQuotas(quotaTenantId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-quotas", quotaTenantId] });
      setQuotaDialogOpen(false);
    }
  });

  const tenants = tenantsQuery.data?.items ?? [];
  const summary: UsageSummary | null = summaryQuery.data ?? null;
  const logs = logsQuery.data?.items ?? [];
  const logsTotal = logsQuery.data?.total ?? 0;
  const quotas: QuotaList | null = quotasQuery.data ?? null;

  useEffect(() => {
    if (quotas && quotaDialogOpen) {
      setQuotaForm({
        tasks_per_month: String(quotas.quotas.tasks_per_month?.limit ?? ""),
        llm_requests_per_month: String(quotas.quotas.llm_requests_per_month?.limit ?? ""),
        workflows_per_month: String(quotas.quotas.workflows_per_month?.limit ?? ""),
        wordpress_sites_per_month: String(quotas.quotas.wordpress_sites_per_month?.limit ?? "")
      });
    }
  }, [quotas, quotaDialogOpen]);

  const handleOpenQuotaEdit = (tid: string) => {
    setQuotaTenantId(tid);
    quotasQuery.refetch();
    setQuotaDialogOpen(true);
  };

  const handleQuotaSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload: {
      tasks_per_month?: number;
      llm_requests_per_month?: number;
      workflows_per_month?: number;
      wordpress_sites_per_month?: number;
    } = {};
    const t = parseInt(quotaForm.tasks_per_month, 10);
    const l = parseInt(quotaForm.llm_requests_per_month, 10);
    const w = parseInt(quotaForm.workflows_per_month, 10);
    const wp = parseInt(quotaForm.wordpress_sites_per_month, 10);
    if (!isNaN(t)) payload.tasks_per_month = t;
    if (!isNaN(l)) payload.llm_requests_per_month = l;
    if (!isNaN(w)) payload.workflows_per_month = w;
    if (!isNaN(wp)) payload.wordpress_sites_per_month = wp;
    if (Object.keys(payload).length === 0) return;
    updateQuotaMutation.mutate(payload);
  };

  return (
    <div className="space-y-8">
      <PageHero
        eyebrow="用量与配额"
        title="租户用量与配额管理"
        description="查看 LLM tokens、流程执行、工具调用用量，并管理租户配额。"
      />

      <section className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-sky-400" />
              用量汇总
            </CardTitle>
            <CardDescription>按租户与日期范围查看用量。</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <FilterBar title="筛选" description="选择租户与日期范围。">
              <select
                className="max-w-[220px] rounded-xl border border-slate-800 bg-slate-900/60 px-3 py-2 text-sm text-slate-100"
                value={tenantId}
                onChange={(e) => setTenantId(e.target.value)}
              >
                <option value="">选择租户</option>
                {tenants.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name} ({t.slug})
                  </option>
                ))}
              </select>
              <Input
                type="date"
                className="max-w-[160px]"
                placeholder="开始日期"
                value={fromDate}
                onChange={(e) => setFromDate(e.target.value)}
              />
              <Input
                type="date"
                className="max-w-[160px]"
                placeholder="结束日期"
                value={toDate}
                onChange={(e) => setToDate(e.target.value)}
              />
            </FilterBar>
            {!tenantId ? (
              <p className="rounded-xl border border-dashed border-slate-700 bg-slate-900/40 py-8 text-center text-sm text-slate-500">
                请选择租户查看用量汇总。
              </p>
            ) : summaryQuery.isLoading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-sky-400" />
              </div>
            ) : summary ? (
              <div className="grid gap-4 sm:grid-cols-2">
                <MetricCard
                  label="LLM Tokens"
                  value={String(summary.llm_tokens_total)}
                  hint={`Prompt: ${summary.llm_prompt_tokens} / Completion: ${summary.llm_completion_tokens}`}
                />
                <MetricCard label="流程执行" value={String(summary.workflow_runs)} />
                <MetricCard label="工具调用" value={String(summary.tool_executions)} />
              </div>
            ) : (
              <p className="text-sm text-slate-500">暂无用量数据。</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>租户配额</CardTitle>
            <CardDescription>查看与编辑租户月度配额。</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {tenants.slice(0, 8).map((t) => (
                <div
                  key={t.id}
                  className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-900/60 p-4"
                >
                  <div>
                    <p className="font-medium text-slate-100">{t.name}</p>
                    <p className="text-xs text-slate-500">{t.slug}</p>
                  </div>
                  <Button variant="outline" size="sm" onClick={() => handleOpenQuotaEdit(t.id)}>
                    编辑配额
                  </Button>
                </div>
              ))}
              {tenants.length > 8 && (
                <p className="text-xs text-slate-500">
                  共 {tenants.length} 个租户，仅展示前 8 个。请从用量汇总选择租户查看配额。
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </section>

      <Card>
        <CardHeader>
          <CardTitle>用量记录</CardTitle>
          <CardDescription>分页查看用量日志。</CardDescription>
        </CardHeader>
        <CardContent>
          <FilterBar title="筛选" description="按租户、类型、日期筛选。">
            <select
              className="max-w-[220px] rounded-xl border border-slate-800 bg-slate-900/60 px-3 py-2 text-sm text-slate-100"
              value={tenantId}
              onChange={(e) => setTenantId(e.target.value)}
            >
              <option value="">全部租户</option>
              {tenants.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
            <select
              className="max-w-[160px] rounded-xl border border-slate-800 bg-slate-900/60 px-3 py-2 text-sm text-slate-100"
              value={usageTypeFilter}
              onChange={(e) => setUsageTypeFilter(e.target.value)}
            >
              <option value="">全部类型</option>
              {USAGE_TYPES.map((u) => (
                <option key={u.value} value={u.value}>
                  {u.label}
                </option>
              ))}
            </select>
            <Input
              type="date"
              className="max-w-[140px]"
              value={fromDate}
              onChange={(e) => setFromDate(e.target.value)}
            />
            <Input
              type="date"
              className="max-w-[140px]"
              value={toDate}
              onChange={(e) => setToDate(e.target.value)}
            />
          </FilterBar>

          {logsQuery.isLoading ? (
            <div className="flex justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-sky-400" />
            </div>
          ) : logs.length === 0 ? (
            <EmptyState
              title="暂无用量记录"
              description="筛选条件下暂无记录。"
              icon={BarChart3}
            />
          ) : (
            <>
              <TableShell>
                <DataTable
                  headers={["时间", "租户", "类型", "Prompt", "Completion", "Quantity"]}
                >
                  {logs.map((log) => {
                    const tenant = tenants.find((t) => t.id === log.tenant_id);
                    return (
                      <DataRow key={log.id}>
                        <DataCell className="whitespace-nowrap text-slate-400">
                          {log.created_at
                            ? format(new Date(log.created_at), "yyyy-MM-dd HH:mm:ss", {
                                locale: zhCN
                              })
                            : "-"}
                        </DataCell>
                        <DataCell className="max-w-[120px] truncate text-slate-300">
                          {tenant?.name ?? log.tenant_id?.slice(0, 8) ?? "-"}
                        </DataCell>
                        <DataCell>
                          <Badge variant="outline" className="font-mono text-xs">
                            {log.usage_type}
                          </Badge>
                        </DataCell>
                        <DataCell className="text-slate-400">{log.prompt_tokens}</DataCell>
                        <DataCell className="text-slate-400">{log.completion_tokens}</DataCell>
                        <DataCell className="text-slate-400">{log.quantity}</DataCell>
                      </DataRow>
                    );
                  })}
                </DataTable>
              </TableShell>
              <div className="mt-4 flex items-center justify-between">
                <p className="text-sm text-slate-400">
                  第 {logsPage * 50 + 1}–{Math.min((logsPage + 1) * 50, logsTotal)} 条，共 {logsTotal} 条
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={logsPage === 0}
                    onClick={() => setLogsPage((p) => Math.max(0, p - 1))}
                  >
                    上一页
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={(logsPage + 1) * 50 >= logsTotal}
                    onClick={() => setLogsPage((p) => p + 1)}
                  >
                    下一页
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Quota Edit Dialog */}
      <Dialog open={quotaDialogOpen} onOpenChange={setQuotaDialogOpen}>
        <DialogContent>
          <form onSubmit={handleQuotaSubmit}>
            <DialogHeader>
              <DialogTitle>编辑租户配额</DialogTitle>
              <DialogDescription>
                {tenants.find((t) => t.id === quotaTenantId)?.name ?? quotaTenantId}
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              {quotas ? (
                <>
                  <div className="space-y-2">
                    <Label>
                      tasks_per_month
                      <span className="ml-2 text-xs text-slate-500">
                        （当前: {quotas.quotas.tasks_per_month?.current ?? 0} / 限额:{" "}
                        {quotas.quotas.tasks_per_month?.limit ?? 0}）
                      </span>
                    </Label>
                    <Input
                      type="number"
                      min={0}
                      placeholder="新限额"
                      value={quotaForm.tasks_per_month}
                      onChange={(e) =>
                        setQuotaForm((f) => ({ ...f, tasks_per_month: e.target.value }))
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>
                      llm_requests_per_month
                      <span className="ml-2 text-xs text-slate-500">
                        （当前: {quotas.quotas.llm_requests_per_month?.current ?? 0} / 限额:{" "}
                        {quotas.quotas.llm_requests_per_month?.limit ?? 0}）
                      </span>
                    </Label>
                    <Input
                      type="number"
                      min={0}
                      placeholder="新限额"
                      value={quotaForm.llm_requests_per_month}
                      onChange={(e) =>
                        setQuotaForm((f) => ({ ...f, llm_requests_per_month: e.target.value }))
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>
                      workflows_per_month
                      <span className="ml-2 text-xs text-slate-500">
                        （当前: {quotas.quotas.workflows_per_month?.current ?? 0} / 限额:{" "}
                        {quotas.quotas.workflows_per_month?.limit ?? 0}）
                      </span>
                    </Label>
                    <Input
                      type="number"
                      min={0}
                      placeholder="新限额"
                      value={quotaForm.workflows_per_month}
                      onChange={(e) =>
                        setQuotaForm((f) => ({ ...f, workflows_per_month: e.target.value }))
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>
                      wordpress_sites_per_month（建站配额）
                      <span className="ml-2 text-xs text-slate-500">
                        （当前: {quotas.quotas.wordpress_sites_per_month?.current ?? 0} / 限额:{" "}
                        {quotas.quotas.wordpress_sites_per_month?.limit ?? 0}）
                      </span>
                    </Label>
                    <Input
                      type="number"
                      min={0}
                      placeholder="新限额"
                      value={quotaForm.wordpress_sites_per_month}
                      onChange={(e) =>
                        setQuotaForm((f) => ({ ...f, wordpress_sites_per_month: e.target.value }))
                      }
                    />
                  </div>
                </>
              ) : quotasQuery.isLoading ? (
                <div className="flex justify-center py-6">
                  <Loader2 className="h-6 w-6 animate-spin text-sky-400" />
                </div>
              ) : (
                <p className="text-sm text-slate-500">加载中…</p>
              )}
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setQuotaDialogOpen(false)}>
                取消
              </Button>
              <Button type="submit" disabled={updateQuotaMutation.isPending}>
                {updateQuotaMutation.isPending && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                保存
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
