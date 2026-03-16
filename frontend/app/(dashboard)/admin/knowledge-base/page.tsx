"use client";

import { useQuery } from "@tanstack/react-query";
import { BookOpen } from "lucide-react";

import {
  PageHero,
  PanelHeader,
  TableShell,
} from "@/components/shared/admin-kit";
import { EmptyState } from "@/components/shared/empty-state";
import { listAdminProjects } from "@/lib/api-admin";

export default function AdminKnowledgeBasePage() {
  const projectsQuery = useQuery({
    queryKey: ["admin-projects-for-kb"],
    queryFn: () => listAdminProjects({ limit: 100 }),
  });

  const projects = (projectsQuery.data?.items ?? []) as Array<{
    id: string;
    name: string;
    key: string;
  }>;

  return (
    <div className="space-y-6">
      <PageHero
        eyebrow="AI员工"
        title="KnowledgeBase"
        description="知识库按项目管理，请到具体项目下创建与配置知识库。"
      />

      <TableShell>
        <div className="p-6">
          <PanelHeader
            title="知识库"
            description="知识库归属于项目。请通过项目空间或项目详情页创建和管理知识库。"
          />
          {projectsQuery.isLoading ? (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-12 text-center text-sm text-slate-400">
              加载中…
            </div>
          ) : projects.length === 0 ? (
            <EmptyState
              title="暂无项目"
              description="请先创建项目，再在项目下配置知识库。"
              icon={BookOpen}
            />
          ) : (
            <div className="space-y-2">
              <p className="text-sm text-slate-400">
                当前平台共 {projects.length} 个项目。知识库需在项目内创建。
              </p>
              <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
                <p className="font-medium text-slate-200">操作说明</p>
                <p className="mt-1 text-sm text-slate-400">
                  前往「项目空间」或「项目管理」选择项目，在项目详情中创建与配置知识库。
                </p>
              </div>
            </div>
          )}
        </div>
      </TableShell>
    </div>
  );
}
