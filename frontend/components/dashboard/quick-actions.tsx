"use client";

import Link from "next/link";
import type { Route } from "next";
import { ArrowRight, Bot, BriefcaseBusiness, GitBranchPlus, ListTodo } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const actions = [
  {
    href: "/projects" as Route,
    title: "新建项目",
    description: "为业务团队创建新的项目空间，统一承载 Agent、任务和流程资产。",
    icon: BriefcaseBusiness
  },
  {
    href: "/agents" as Route,
    title: "创建智能员工",
    description: "快速配置智能员工的角色、模型、提示词与工具权限。",
    icon: Bot
  },
  {
    href: "/tasks" as Route,
    title: "发起任务",
    description: "将业务需求投递到执行队列，并分配给 Agent 或流程处理。",
    icon: ListTodo
  },
  {
    href: "/workflow-builder" as Route,
    title: "编排流程",
    description: "搭建带有分支、条件和延时的自动化执行链路。",
    icon: GitBranchPlus
  }
];

export function QuickActions() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>快捷入口</CardTitle>
        <CardDescription>面向运营、实施与交付角色的常用入口，强调“先配置、再投递、后追踪”的后台操作路径。</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-4 md:grid-cols-2">
        {actions.map((action) => (
          <div key={action.href} className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <div className="flex items-start justify-between gap-4">
              <div className="rounded-2xl border border-sky-500/20 bg-sky-500/10 p-3">
                <action.icon className="h-5 w-5 text-sky-300" />
              </div>
              <Button asChild size="sm" variant="outline">
                <Link href={action.href}>
                  进入
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </div>
            <h3 className="mt-4 text-base font-semibold text-slate-100">{action.title}</h3>
            <p className="mt-2 text-sm leading-6 text-slate-400">{action.description}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
