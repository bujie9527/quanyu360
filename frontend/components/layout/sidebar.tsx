"use client";

import type { Route } from "next";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronDown, ChevronRight } from "lucide-react";
import { useMemo, useState } from "react";

import { cn } from "@/lib/utils";
import { adminNavigationItems, navigationItems } from "@/lib/navigation";

function isInGroup(href: string, children: { href: string }[]): boolean {
  return children.some((c) => href === c.href || href?.startsWith(c.href + "/"));
}

export function Sidebar() {
  const pathname = usePathname();
  const isAdmin = pathname?.startsWith("/admin");
  const items = isAdmin ? adminNavigationItems : navigationItems;
  const title = isAdmin ? "平台管理" : "运营管理控制台";
  const subtitle = isAdmin
    ? "管理租户、用户与系统配置。"
    : "面向中国 SaaS 场景统一管理项目空间、智能员工、任务队列和流程执行。";

  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});
  const initExpanded = useMemo(() => {
    const next: Record<string, boolean> = {};
    items.forEach((item) => {
      if ("type" in item && item.type === "group" && "children" in item) {
        next[item.label] = isInGroup(pathname ?? "", item.children);
      }
    });
    return next;
  }, [items, pathname]);

  const isExpanded = (label: string) =>
    collapsed[label] !== undefined ? !collapsed[label] : (initExpanded[label] ?? true);

  const toggleGroup = (label: string) => {
    setCollapsed((prev) => ({ ...prev, [label]: isExpanded(label) }));
  };

  return (
    <aside className="hidden w-72 flex-col border-r border-slate-800 p-6 lg:flex">
      <div className="space-y-3">
        <h1 className="text-2xl font-semibold text-slate-100">{title}</h1>
        <p className="text-sm leading-6 text-slate-400">{subtitle}</p>
      </div>

      <nav className="mt-10 space-y-2">
        {items.map((item, idx) =>
          "type" in item && item.type === "group" ? (
            <div key={item.label} className="space-y-1">
              <button
                type="button"
                onClick={() => toggleGroup(item.label)}
                className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs font-medium uppercase tracking-wider text-slate-500 transition-colors hover:text-slate-400"
              >
                {isExpanded(item.label) ? (
                  <ChevronDown className="h-3.5 w-3.5 shrink-0" />
                ) : (
                  <ChevronRight className="h-3.5 w-3.5 shrink-0" />
                )}
                {(() => {
                  const GroupIcon = item.icon;
                  return <GroupIcon className="h-3.5 w-3.5 shrink-0" />;
                })()}
                {item.label}
              </button>
              {isExpanded(item.label) &&
                item.children.map((child) => (
                  <Link
                    key={child.href}
                    href={child.href as Route}
                    className={cn(
                      "ml-4 flex items-start gap-3 rounded-xl border px-3 py-3 text-sm text-slate-300 transition-all duration-150",
                      pathname === child.href
                        ? "border-sky-500/30 bg-sky-500/10 shadow-[inset_3px_0_0_0_rgba(56,189,248,0.9)]"
                        : "border-transparent hover:border-slate-700 hover:bg-slate-900/80 active:bg-slate-800"
                    )}
                  >
                    <div className="min-w-0 flex-1">
                      <p className="font-medium text-slate-100">{child.label}</p>
                      <p className="text-xs text-slate-400">{child.description}</p>
                    </div>
                  </Link>
                ))}
            </div>
          ) : (
            <Link
              key={"href" in item ? item.href : idx}
              href={(item as { href: string }).href as Route}
              className={cn(
                "flex items-start gap-3 rounded-xl border px-3 py-3 text-sm text-slate-300 transition-all duration-150",
                pathname === (item as { href: string }).href
                  ? "border-sky-500/30 bg-sky-500/10 shadow-[inset_3px_0_0_0_rgba(56,189,248,0.9)]"
                  : "border-transparent hover:border-slate-700 hover:bg-slate-900/80 active:bg-slate-800"
              )}
            >
              {(() => {
                const linkItem = item as { href: string; icon: React.ComponentType<{ className?: string }> };
                const Icon = linkItem.icon;
                return <Icon className={cn("mt-0.5 h-4 w-4", pathname === linkItem.href ? "text-sky-300" : "text-slate-500")} />;
              })()}
              <div>
                <p className="font-medium text-slate-100">{item.label}</p>
                <p className="text-xs text-slate-400">{item.description}</p>
              </div>
            </Link>
          )
        )}
      </nav>
    </aside>
  );
}
