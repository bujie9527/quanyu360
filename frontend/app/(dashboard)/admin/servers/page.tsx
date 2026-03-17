"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Loader2, Plus, Server as ServerIcon, Terminal, Trash2, Wifi, Wrench, XCircle } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  createServer,
  deleteServer,
  listServers,
  testServer,
  type ServerItem,
} from "@/lib/api-admin";

const ADMIN_BASE =
  process.env.NEXT_PUBLIC_API_GATEWAY_URL ??
  process.env.NEXT_PUBLIC_PROJECT_SERVICE_URL ??
  "http://localhost:8300";

async function triggerSetup(serverId: string): Promise<{ success: boolean; message: string; setup_log: string }> {
  const res = await fetch(`${ADMIN_BASE}/api/admin/servers/${serverId}/setup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error(`Setup failed: ${res.status}`);
  return res.json();
}

async function getSetupLog(serverId: string): Promise<{ success: boolean; message: string; setup_log: string }> {
  const res = await fetch(`${ADMIN_BASE}/api/admin/servers/${serverId}/setup-log`);
  if (!res.ok) throw new Error(`Log fetch failed: ${res.status}`);
  return res.json();
}

function SetupStatusBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; cls: string }> = {
    pending:      { label: "待初始化", cls: "bg-slate-700 text-slate-300" },
    running:      { label: "初始化中", cls: "bg-yellow-900 text-yellow-300" },
    completed:    { label: "已就绪",   cls: "bg-emerald-900 text-emerald-300" },
    failed:       { label: "失败",     cls: "bg-red-900 text-red-300" },
  };
  const { label, cls } = map[status] ?? { label: status, cls: "bg-slate-700 text-slate-300" };
  return <span className={`rounded px-2 py-0.5 text-xs font-medium ${cls}`}>{label}</span>;
}

export default function AdminServersPage() {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({
    name: "",
    host: "",
    port: 22,
    ssh_user: "root",
    ssh_password: "",
  });
  const [selectedServerId, setSelectedServerId] = useState<string | null>(null);
  const [setupLog, setSetupLog] = useState<string>("");
  const [pollingId, setPollingId] = useState<ReturnType<typeof setInterval> | null>(null);

  const serversQuery = useQuery({
    queryKey: ["admin-servers"],
    queryFn: () => listServers({ limit: 200 }),
    refetchInterval: 5000,
  });

  const createMutation = useMutation({
    mutationFn: createServer,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-servers"] });
      setForm({ name: "", host: "", port: 22, ssh_user: "root", ssh_password: "" });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteServer,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-servers"] }),
  });

  const testMutation = useMutation({ mutationFn: testServer });

  const setupMutation = useMutation({
    mutationFn: triggerSetup,
    onSuccess: (_, serverId) => {
      setSelectedServerId(serverId);
      setSetupLog("环境初始化已启动，请稍候...\n");
      // Start polling for log updates
      const id = setInterval(async () => {
        try {
          const data = await getSetupLog(serverId);
          setSetupLog(data.setup_log || "");
          queryClient.invalidateQueries({ queryKey: ["admin-servers"] });
          if (data.message === "completed" || data.message === "failed") {
            clearInterval(id);
            setPollingId(null);
          }
        } catch {
          // ignore transient errors
        }
      }, 3000);
      setPollingId(id);
    },
  });

  const selectedServer = (serversQuery.data?.items ?? []).find((s) => s.id === selectedServerId);

  const canCreate = !!form.name && !!form.host && !!form.ssh_password && !createMutation.isPending;

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm text-slate-400">Admin / 建站中心</p>
        <h1 className="text-2xl font-semibold text-slate-100">服务器管理</h1>
      </div>

      {/* Create Form - simplified to SSH essentials only */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Plus className="h-5 w-5" />
            新建服务器
          </CardTitle>
          <CardDescription>
            只需填写 SSH 连接信息。添加后点击"初始化环境"，系统将自动安装
            Nginx + PHP 8.2 + MariaDB 10.11 + WP-CLI 标准环境。
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          <div>
            <Label>名称 <span className="text-red-400">*</span></Label>
            <Input
              placeholder="例：建站服务器-01"
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            />
          </div>
          <div>
            <Label>主机 IP <span className="text-red-400">*</span></Label>
            <Input
              placeholder="43.160.237.155"
              value={form.host}
              onChange={(e) => setForm((f) => ({ ...f, host: e.target.value }))}
            />
          </div>
          <div>
            <Label>SSH 端口</Label>
            <Input
              type="number"
              value={form.port}
              onChange={(e) => setForm((f) => ({ ...f, port: Number(e.target.value) || 22 }))}
            />
          </div>
          <div>
            <Label>SSH 用户</Label>
            <Input
              value={form.ssh_user}
              onChange={(e) => setForm((f) => ({ ...f, ssh_user: e.target.value }))}
            />
          </div>
          <div>
            <Label>SSH 密码 <span className="text-red-400">*</span></Label>
            <Input
              type="password"
              placeholder="服务器 root 密码"
              value={form.ssh_password}
              onChange={(e) => setForm((f) => ({ ...f, ssh_password: e.target.value }))}
            />
          </div>
          <div className="flex items-end">
            <Button
              className="w-full"
              disabled={!canCreate}
              onClick={() =>
                createMutation.mutate({
                  name: form.name,
                  host: form.host,
                  port: form.port,
                  ssh_user: form.ssh_user,
                  ssh_password: form.ssh_password,
                  status: "pending_setup",
                })
              }
            >
              {createMutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Plus className="mr-2 h-4 w-4" />}
              添加服务器
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 xl:grid-cols-[1fr_480px]">
        {/* Server List */}
        <Card>
          <CardHeader>
            <CardTitle>服务器列表</CardTitle>
            <CardDescription>点击"初始化环境"自动安装 LEMP + WP-CLI 标准栈</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {(serversQuery.data?.items ?? []).map((s: ServerItem) => (
              <div
                key={s.id}
                className={`rounded-lg border p-3 transition-colors ${
                  selectedServerId === s.id
                    ? "border-emerald-600 bg-slate-800"
                    : "border-slate-800 bg-slate-900/50"
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <p className="flex items-center gap-2 text-sm font-medium text-slate-100">
                      <ServerIcon className="h-4 w-4 shrink-0" />
                      {s.name}
                      <SetupStatusBadge status={s.setup_status ?? "pending"} />
                    </p>
                    <p className="mt-0.5 text-xs text-slate-400">
                      {s.host}:{s.port} · {s.ssh_user}
                    </p>
                    {s.mysql_admin_user && (
                      <p className="mt-0.5 text-xs text-slate-500">
                        MySQL: {s.mysql_admin_user}@{s.mysql_host ?? "localhost"}
                      </p>
                    )}
                  </div>
                  <div className="flex shrink-0 flex-wrap gap-1.5">
                    {/* Setup button — shown when not yet completed */}
                    {s.setup_status !== "completed" && s.setup_status !== "running" && (
                      <Button
                        size="sm"
                        className="bg-emerald-700 hover:bg-emerald-600"
                        onClick={() => setupMutation.mutate(s.id)}
                        disabled={setupMutation.isPending}
                      >
                        <Wrench className="mr-1 h-3.5 w-3.5" />
                        初始化环境
                      </Button>
                    )}
                    {s.setup_status === "running" && (
                      <Button size="sm" variant="outline" onClick={() => setSelectedServerId(s.id)}>
                        <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />
                        查看日志
                      </Button>
                    )}
                    {s.setup_status === "completed" && (
                      <Button size="sm" variant="outline" onClick={() => setSelectedServerId(s.id)}>
                        <Terminal className="mr-1 h-3.5 w-3.5" />
                        查看日志
                      </Button>
                    )}
                    <Button size="sm" variant="outline" onClick={() => testMutation.mutate(s.id)}>
                      <Wifi className="mr-1 h-3.5 w-3.5" />
                      测试
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-red-400 hover:text-red-300"
                      onClick={() => deleteMutation.mutate(s.id)}
                    >
                      <Trash2 className="mr-1 h-3.5 w-3.5" />
                      删除
                    </Button>
                  </div>
                </div>
              </div>
            ))}
            {(serversQuery.data?.items ?? []).length === 0 && (
              <p className="text-sm text-slate-500">暂无服务器，请点击上方"添加服务器"。</p>
            )}
            {testMutation.data && (
              <p className={`flex items-center gap-1 text-sm ${testMutation.data.success ? "text-emerald-400" : "text-red-400"}`}>
                {testMutation.data.success ? <CheckCircle2 className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
                {testMutation.data.message}
              </p>
            )}
          </CardContent>
        </Card>

        {/* Setup Log Panel */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Terminal className="h-5 w-5" />
              环境初始化日志
            </CardTitle>
            <CardDescription>
              {selectedServer
                ? `${selectedServer.name} · ${selectedServer.setup_status ?? "pending"}`
                : "选择服务器后点击"初始化环境"查看实时日志"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <pre className="max-h-[500px] min-h-[200px] overflow-y-auto rounded border border-slate-700 bg-slate-950 p-3 text-xs text-slate-300 whitespace-pre-wrap">
              {setupLog || selectedServer?.setup_log || "暂无日志"}
            </pre>
            {selectedServer?.setup_status === "completed" && (
              <p className="mt-2 flex items-center gap-1 text-sm text-emerald-400">
                <CheckCircle2 className="h-4 w-4" />
                环境初始化完成，服务器已就绪，可用于批量建站。
              </p>
            )}
            {selectedServer?.setup_status === "failed" && (
              <p className="mt-2 flex items-center gap-1 text-sm text-red-400">
                <XCircle className="h-4 w-4" />
                初始化失败，请查看日志排查问题后重试。
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
