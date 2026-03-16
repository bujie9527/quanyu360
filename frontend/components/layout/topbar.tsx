"use client";

import { Bell, LogOut } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { pageMeta } from "@/lib/navigation";
import { clearToken, getUser, isAuthenticated } from "@/lib/auth";

export function Topbar() {
  const pathname = usePathname();
  const router = useRouter();
  const isAdmin = pathname?.startsWith("/admin");
  const meta = pageMeta[pathname] ?? (isAdmin ? pageMeta["/admin"] : pageMeta["/dashboard"]);
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);
  const user = mounted ? getUser() : null;
  const hasAuth = mounted && isAuthenticated();

  const handleLogout = () => {
    clearToken();
    router.replace("/login");
  };

  return (
    <div className="fixed left-0 right-0 top-0 z-40 h-16 border-b border-slate-800 bg-slate-900/40 backdrop-blur lg:left-72">
      <div className="flex h-full items-center justify-between px-6 md:px-8">
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <span>{isAdmin ? "Platform Admin" : "工作台"}</span>
          <span>/</span>
          <span className="font-medium text-slate-100">{meta.title}</span>
        </div>
        <div className="flex items-center gap-3">
          {hasAuth && user && (
            <span className="text-xs text-slate-500">
              {user.email} @ {user.tenant_slug}
            </span>
          )}
          <button
            className="flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-slate-300 shadow-sm transition-all duration-150 hover:border-slate-700 hover:bg-slate-800 active:scale-[0.98] active:bg-slate-700"
            aria-label="消息中心"
          >
            <Bell className="h-4 w-4" />
            <span className="hidden sm:inline">消息中心</span>
          </button>
          {hasAuth ? (
            <button
              type="button"
              onClick={handleLogout}
              className="flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-slate-300 transition hover:border-slate-700 hover:bg-slate-800"
            >
              <LogOut className="h-4 w-4" />
              <span className="hidden sm:inline">退出登录</span>
            </button>
          ) : (
            <Link
              href="/login"
              className="flex items-center gap-2 rounded-xl border border-sky-500/40 bg-sky-500/20 px-3 py-2 text-sm text-sky-200 transition hover:bg-sky-500/30"
            >
              登录
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}
