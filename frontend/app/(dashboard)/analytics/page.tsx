"use client";

import { AnalyticsDashboard } from "@/components/dashboard/analytics-dashboard";
import { HeroTip, PageHero } from "@/components/shared/admin-kit";

export default function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <PageHero
        eyebrow="数据分析"
        title="Analytics Dashboard"
        description="任务执行、Agent 性能与系统使用情况的可视化分析。"
      >
        <HeroTip label="任务执行" value="状态分布、趋势与耗时对比" />
        <HeroTip label="Agent 性能" value="成功率、耗时与 Token 消耗" />
        <HeroTip label="系统使用" value="服务健康、资源消耗" />
      </PageHero>
      <AnalyticsDashboard />
    </div>
  );
}
