"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import {
  Activity,
  ArrowRight,
  BarChart3,
  Bot,
  BriefcaseBusiness,
  CheckCircle2,
  GitBranchPlus,
  ListTodo,
  Shield,
  ShieldCheck,
  Users
} from "lucide-react";

import { MetricCard, PageHero } from "@/components/shared/admin-kit";
import { StatusBadge } from "@/components/shared/status-badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getAdminDashboard } from "@/lib/api-admin";

const quickLinks = [
  { href: "/admin/tenants", label: "租户管理", desc: "创建与管理组织", icon: BriefcaseBusiness },
  { href: "/admin/users", label: "用户管理", desc: "查看与管理用户", icon: Users },
  { href: "/admin/roles", label: "角色管理", desc: "RBAC 角色", icon: Shield },
  { href: "/admin/projects", label: "项目管理", desc: "查看所有项目", icon: Activity },
  { href: "/admin/agents", label: "Agent 管理", desc: "查看所有 Agent", icon: Bot },
  { href: "/admin/tasks", label: "任务管理", desc: "查看所有任务", icon: ListTodo },
  { href: "/admin/workflows", label: "流程管理", desc: "查看所有工作流", icon: GitBranchPlus },
  { href: "/admin/usage", label: "用量与配额", desc: "租户用量与配额", icon: BarChart3 },
  { href: "/admin/audit", label: "审计日志", desc: "AI 行为审计记录", icon: ShieldCheck },
  { href: "/admin/settings", label: "系统设置", desc: "平台配置", icon: Shield }
] as const;

export default function AdminDashboardPage() {
  const dashboardQuery = useQuery({
    queryKey: ["admin-dashboard"],
    queryFn: getAdminDashboard
  });

  const data = dashboardQuery.data;
  const stats = [
    { label: "用户总数", value: String(data?.total_users ?? 0), icon: Users },
    { label: "租户总数", value: String(data?.total_tenants ?? 0), icon: BriefcaseBusiness },
    { label: "项目总数", value: String(data?.total_projects ?? 0), icon: Activity },
    { label: "Agent 总数", value: String(data?.total_agents ?? 0), icon: Bot }
  ];

  const healthEntries = data?.system_health
    ? Object.entries(data.system_health).map(([key, val]) => ({ name: key, status: val }))
    : [];
  const allHealthy = healthEntries.every((e) => e.status === "ok" || e.status === "healthy");

  return (
    <div className="space-y-8">
      <PageHero
        eyebrow="平台管理"
        title="管理概览"
        description="平台统计、系统健康与管理总览。"
      />

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map((s) => (
          <MetricCard
            key={s.label}
            label={s.label}
            value={s.value}
            icon={s.icon}
          />
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-start justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5 text-sky-300" />
                系统健康
              </CardTitle>
              <CardDescription>服务状态与可用性</CardDescription>
            </div>
            {healthEntries.length > 0 && (
              <span className={`flex items-center gap-1.5 text-xs font-medium ${allHealthy ? "text-emerald-400" : "text-amber-400"}`}>
                {allHealthy ? <CheckCircle2 className="h-4 w-4" /> : null}
                {allHealthy ? "系统运行正常" : "存在问题"}
              </span>
            )}
          </CardHeader>
          <CardContent className="space-y-3">
            {dashboardQuery.isLoading ? (
              <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-8 text-center text-sm text-slate-400">
                加载中…
              </div>
            ) : healthEntries.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-slate-700 bg-slate-900/60 p-8 text-center text-sm text-slate-500">
                暂无健康数据
              </div>
            ) : (
              <div className="space-y-2">
                {healthEntries.map(({ name, status }) => (
                  <div
                    key={name}
                    className="flex flex-col gap-2 rounded-xl border border-slate-800 bg-slate-900/70 p-4 sm:flex-row sm:items-center sm:justify-between"
                  >
                    <p className="font-medium text-slate-100">{name}</p>
                    <StatusBadge value={status} />
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>概览</CardTitle>
              <CardDescription>平台使用量与任务统计。</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
                <p className="text-sm text-slate-400">任务总数</p>
                <p className="mt-2 text-3xl font-semibold text-slate-100">{data?.total_tasks ?? 0}</p>
              </div>
            </CardContent>
          </Card>

          <Card className="border-violet-500/20 bg-violet-500/5">
            <CardHeader>
              <CardTitle className="text-slate-100">快捷入口</CardTitle>
              <CardDescription>跳转到管理模块。</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {quickLinks.map(({ href, label, desc, icon: Icon }) => (
                <Link
                  key={href}
                  href={href}
                  className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-900/60 p-4 transition-colors hover:border-slate-700 hover:bg-slate-800/60"
                >
                  <div className="flex items-center gap-3">
                    <div className="rounded-lg border border-violet-500/20 bg-violet-500/10 p-2">
                      <Icon className="h-4 w-4 text-violet-300" />
                    </div>
                    <div>
                      <p className="font-medium text-slate-100">{label}</p>
                      <p className="text-xs text-slate-400">{desc}</p>
                    </div>
                  </div>
                  <ArrowRight className="h-4 w-4 text-slate-500" />
                </Link>
              ))}
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  );
}
