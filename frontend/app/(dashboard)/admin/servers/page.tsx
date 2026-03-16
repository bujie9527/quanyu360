"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Plus, Server as ServerIcon, Trash2, Wifi } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { createServer, deleteServer, listServers, testServer } from "@/lib/api-admin";

export default function AdminServersPage() {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({
    name: "",
    host: "",
    port: 22,
    ssh_user: "root",
    ssh_password: "",
    web_root: "/www/wwwroot",
    mysql_admin_user: "root",
    mysql_admin_password: "",
  });

  const serversQuery = useQuery({
    queryKey: ["admin-servers"],
    queryFn: () => listServers({ limit: 200 }),
  });

  const createMutation = useMutation({
    mutationFn: createServer,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-servers"] });
      setForm({
        name: "",
        host: "",
        port: 22,
        ssh_user: "root",
        ssh_password: "",
        web_root: "/www/wwwroot",
        mysql_admin_user: "root",
        mysql_admin_password: "",
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteServer,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-servers"] }),
  });

  const testMutation = useMutation({
    mutationFn: testServer,
  });

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm text-slate-400">Admin / Servers</p>
        <h1 className="text-2xl font-semibold text-slate-100">服务器管理</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Plus className="h-5 w-5" />
            新建服务器
          </CardTitle>
          <CardDescription>配置 SSH 与 MySQL 管理信息，供 WP-CLI 自动建站使用。</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2">
          <div><Label>名称</Label><Input value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} /></div>
          <div><Label>主机</Label><Input value={form.host} onChange={(e) => setForm((f) => ({ ...f, host: e.target.value }))} /></div>
          <div><Label>SSH 端口</Label><Input type="number" value={form.port} onChange={(e) => setForm((f) => ({ ...f, port: Number(e.target.value) || 22 }))} /></div>
          <div><Label>SSH 用户</Label><Input value={form.ssh_user} onChange={(e) => setForm((f) => ({ ...f, ssh_user: e.target.value }))} /></div>
          <div><Label>SSH 密码</Label><Input type="password" value={form.ssh_password} onChange={(e) => setForm((f) => ({ ...f, ssh_password: e.target.value }))} /></div>
          <div><Label>Web Root</Label><Input value={form.web_root} onChange={(e) => setForm((f) => ({ ...f, web_root: e.target.value }))} /></div>
          <div><Label>MySQL 管理员</Label><Input value={form.mysql_admin_user} onChange={(e) => setForm((f) => ({ ...f, mysql_admin_user: e.target.value }))} /></div>
          <div><Label>MySQL 密码</Label><Input type="password" value={form.mysql_admin_password} onChange={(e) => setForm((f) => ({ ...f, mysql_admin_password: e.target.value }))} /></div>
          <div className="md:col-span-2">
            <Button
              disabled={!form.name || !form.host || !form.mysql_admin_password || createMutation.isPending}
              onClick={() =>
                createMutation.mutate({
                  ...form,
                  php_bin: "php",
                  wp_cli_bin: "wp",
                  mysql_host: "localhost",
                  mysql_port: 3306,
                  mysql_db_prefix: "wp_",
                  status: "active",
                })
              }
            >
              {createMutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              创建服务器
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>服务器列表</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {(serversQuery.data?.items ?? []).map((s) => (
            <div key={s.id} className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-900/50 p-3">
              <div>
                <p className="flex items-center gap-2 text-sm font-medium text-slate-100">
                  <ServerIcon className="h-4 w-4" />
                  {s.name}
                </p>
                <p className="text-xs text-slate-400">{s.host}:{s.port} · {s.ssh_user} · {s.status}</p>
              </div>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={() => testMutation.mutate(s.id)}>
                  <Wifi className="mr-1 h-3.5 w-3.5" />
                  测试
                </Button>
                <Button size="sm" variant="outline" className="text-red-400" onClick={() => deleteMutation.mutate(s.id)}>
                  <Trash2 className="mr-1 h-3.5 w-3.5" />
                  删除
                </Button>
              </div>
            </div>
          ))}
          {(serversQuery.data?.items ?? []).length === 0 && (
            <p className="text-sm text-slate-500">暂无服务器配置</p>
          )}
          {testMutation.data && (
            <p className={`text-sm ${testMutation.data.success ? "text-emerald-400" : "text-red-400"}`}>
              {testMutation.data.message}
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
