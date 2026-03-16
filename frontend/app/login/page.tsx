"use client";

import { useMutation } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { setToken, setUser } from "@/lib/auth";

const AUTH_BASE = process.env.NEXT_PUBLIC_AUTH_SERVICE_URL ?? "http://localhost:8001";
// 登录接口路径：auth 基础 URL 已含 /api/auth 时仅追加 /login，避免 /api/auth/auth/login
const AUTH_LOGIN_PATH = /\/api\/auth\/?$/.test(AUTH_BASE)
  ? "/login"
  : (process.env.NEXT_PUBLIC_AUTH_SERVICE_URL === process.env.NEXT_PUBLIC_API_GATEWAY_URL ||
     /:8300(\/|$)/.test(AUTH_BASE))
    ? "/api/auth/login"
    : "/auth/login";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectTo = searchParams.get("redirect") ?? "/dashboard";
  const [tenantSlug, setTenantSlug] = useState("demo-enterprise");
  const [email, setEmail] = useState("owner@demo-enterprise.ai");
  const [password, setPassword] = useState("");

  const loginMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${AUTH_BASE}${AUTH_LOGIN_PATH}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tenant_slug: tenantSlug, email, password })
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? `登录失败: ${res.status}`);
      }
      return res.json() as Promise<{
        access_token: string;
        user: { id: string; tenant_id: string; tenant_slug: string; email: string };
      }>;
    },
    onSuccess: (data) => {
      setToken(data.access_token);
      setUser(data.user);
      // redirectTo 来自 URL 参数，typedRoutes 需断言
      router.replace(redirectTo as "/dashboard");
    }
  });

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 p-4">
      <Card className="w-full max-w-md border-slate-800 bg-slate-900">
        <CardHeader>
          <CardTitle className="text-slate-100">登录 - 全宇企业智能营销系统</CardTitle>
          <CardDescription>使用租户账号登录，获取统一鉴权凭证</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              loginMutation.mutate();
            }}
            className="space-y-4"
          >
            <div>
              <label className="mb-2 block text-sm font-medium text-slate-300">租户标识</label>
              <Input
                value={tenantSlug}
                onChange={(e) => setTenantSlug(e.target.value)}
                placeholder="demo-enterprise"
                className="border-slate-700 bg-slate-900 text-slate-100"
                required
              />
            </div>
            <div>
              <label className="mb-2 block text-sm font-medium text-slate-300">邮箱</label>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="owner@demo-enterprise.ai"
                className="border-slate-700 bg-slate-900 text-slate-100"
                required
              />
            </div>
            <div>
              <label className="mb-2 block text-sm font-medium text-slate-300">密码</label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="ChangeMe123!"
                className="border-slate-700 bg-slate-900 text-slate-100"
                required
              />
              <p className="mt-1 text-xs text-slate-500">演示账号默认密码: ChangeMe123!</p>
            </div>
            {loginMutation.isError && (
              <p className="text-sm text-red-400">{String(loginMutation.error)}</p>
            )}
            <Button
              type="submit"
              className="w-full"
              disabled={loginMutation.isPending}
            >
              {loginMutation.isPending ? "登录中…" : "登录"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-slate-950">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-sky-500 border-t-transparent" />
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
