"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Play, Server, TerminalSquare } from "lucide-react";
import { useMemo, useState } from "react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  batchInstallSites,
  getSiteInstallRun,
  listInstallWorkflows,
  listPlatformDomains,
  listServers,
  listSitePoolSites,
  type SitePoolSiteItem,
} from "@/lib/api-admin";

export default function AdminSiteInstallPage() {
  const queryClient = useQueryClient();
  const [serverId, setServerId] = useState("");
  const [workflowId, setWorkflowId] = useState("");
  const [domainIds, setDomainIds] = useState<string[]>([]);
  const [adminUser, setAdminUser] = useState("admin");
  const [adminPassword, setAdminPassword] = useState("");
  const [adminEmail, setAdminEmail] = useState("");
  const [titlePrefix, setTitlePrefix] = useState("Matrix Site");
  const [selectedSiteId, setSelectedSiteId] = useState("");

  const serversQuery = useQuery({
    queryKey: ["admin-servers"],
    queryFn: () => listServers({ status: "active", limit: 200 }),
  });

  const domainsQuery = useQuery({
    queryKey: ["admin-platform-domains-available"],
    queryFn: () => listPlatformDomains({ status: "available", limit: 500 }),
  });

  const workflowsQuery = useQuery({
    queryKey: ["admin-install-workflows"],
    queryFn: () => listInstallWorkflows(),
  });

  const poolQuery = useQuery({
    queryKey: ["admin-site-pool-installing"],
    queryFn: () => listSitePoolSites({ assigned: false, limit: 50 }),
    refetchInterval: 3000,
  });

  const selectedSite = useMemo(
    () => (poolQuery.data?.items ?? []).find((s) => s.id === selectedSiteId) ?? null,
    [poolQuery.data, selectedSiteId]
  );

  const runQuery = useQuery({
    queryKey: ["admin-site-install-run", selectedSiteId],
    queryFn: () => getSiteInstallRun(selectedSiteId),
    enabled: !!selectedSiteId,
    refetchInterval: selectedSite?.pool_status === "installing" ? 3000 : false,
  });

  const installMutation = useMutation({
    mutationFn: batchInstallSites,
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["admin-site-pool-installing"] });
      queryClient.invalidateQueries({ queryKey: ["admin-platform-domains-available"] });
      if (result.site_ids[0]) setSelectedSiteId(result.site_ids[0]);
      setDomainIds([]);
    },
  });

  const canSubmit =
    !!serverId &&
    !!workflowId &&
    domainIds.length > 0 &&
    !!adminUser.trim() &&
    !!adminPassword.trim() &&
    !!adminEmail.trim() &&
    !installMutation.isPending;

  const toggleDomain = (id: string) => {
    setDomainIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  };

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm text-slate-400">Admin / 建站中心</p>
        <h1 className="text-2xl font-semibold text-slate-100">批量建站</h1>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Server className="h-5 w-5" />
              安装参数
            </CardTitle>
            <CardDescription>选择服务器、域名和标准化管理员配置后，批量安装 WordPress。</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>服务器</Label>
              <select className="mt-2 w-full rounded border border-slate-700 bg-slate-900 px-3 py-2" value={serverId} onChange={(e) => setServerId(e.target.value)}>
                <option value="">选择服务器</option>
                {(serversQuery.data?.items ?? []).map((s) => (
                  <option key={s.id} value={s.id}>{s.name} ({s.host}:{s.port})</option>
                ))}
              </select>
            </div>

            <div>
              <Label>安装工作流</Label>
              <select className="mt-2 w-full rounded border border-slate-700 bg-slate-900 px-3 py-2" value={workflowId} onChange={(e) => setWorkflowId(e.target.value)}>
                <option value="">选择工作流</option>
                {(workflowsQuery.data?.items ?? []).map((wf) => (
                  <option key={wf.id} value={wf.id}>{wf.name} ({wf.slug})</option>
                ))}
              </select>
            </div>

            <div className="grid gap-3 md:grid-cols-2">
              <div>
                <Label>管理员用户名</Label>
                <Input value={adminUser} onChange={(e) => setAdminUser(e.target.value)} />
              </div>
              <div>
                <Label>管理员邮箱</Label>
                <Input value={adminEmail} onChange={(e) => setAdminEmail(e.target.value)} />
              </div>
              <div>
                <Label>管理员密码</Label>
                <Input type="password" value={adminPassword} onChange={(e) => setAdminPassword(e.target.value)} />
              </div>
              <div>
                <Label>站点标题前缀</Label>
                <Input value={titlePrefix} onChange={(e) => setTitlePrefix(e.target.value)} />
              </div>
            </div>

            <div>
              <Label>域名（可多选）</Label>
              <div className="mt-2 max-h-48 space-y-1 overflow-y-auto rounded border border-slate-700 p-2">
                {(domainsQuery.data?.items ?? []).map((d) => (
                  <label key={d.id} className="flex cursor-pointer items-center gap-2 rounded px-2 py-1 hover:bg-slate-800">
                    <input type="checkbox" checked={domainIds.includes(d.id)} onChange={() => toggleDomain(d.id)} />
                    <span className="text-sm text-slate-200">{d.domain}</span>
                  </label>
                ))}
              </div>
            </div>

            <button
              className="inline-flex items-center rounded bg-emerald-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
              disabled={!canSubmit}
              onClick={() =>
                installMutation.mutate({
                  server_id: serverId,
                  domain_ids: domainIds,
                  workflow_id: workflowId,
                  admin_username: adminUser,
                  admin_password: adminPassword,
                  admin_email: adminEmail,
                  site_title_prefix: titlePrefix,
                })
              }
            >
              {installMutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Play className="mr-2 h-4 w-4" />}
              开始批量建站
            </button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TerminalSquare className="h-5 w-5" />
              安装日志（实时）
            </CardTitle>
            <CardDescription>选择左侧触发后的站点，查看步骤执行日志。</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              {(poolQuery.data?.items ?? []).map((site: SitePoolSiteItem) => (
                <button
                  key={site.id}
                  className={`w-full rounded border px-3 py-2 text-left text-sm ${selectedSiteId === site.id ? "border-emerald-500 bg-slate-800" : "border-slate-700 bg-slate-900"}`}
                  onClick={() => setSelectedSiteId(site.id)}
                >
                  <p className="font-medium text-slate-100">{site.domain}</p>
                  <p className="text-xs text-slate-400">{site.pool_status} · {site.status}</p>
                </button>
              ))}
              {(poolQuery.data?.items ?? []).length === 0 && <p className="text-sm text-slate-500">暂无待安装/待分配站点</p>}
            </div>

            {runQuery.data && (
              <div className="max-h-72 space-y-2 overflow-y-auto rounded border border-slate-700 p-2">
                <p className="text-xs text-slate-400">TaskRun: {runQuery.data.task_run_id} · {runQuery.data.status}</p>
                {runQuery.data.steps.map((step) => (
                  <div key={step.id} className="rounded border border-slate-800 bg-slate-900/50 p-2 text-xs">
                    <p className="text-slate-200">{step.step_name} · {step.status}</p>
                    <pre className="mt-1 whitespace-pre-wrap text-slate-400">{JSON.stringify(step.output_json ?? {}, null, 2)}</pre>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
