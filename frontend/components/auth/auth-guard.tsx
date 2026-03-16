"use client";

import { useRouter, usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { isAuthenticated } from "@/lib/auth";

const LOGIN_PATH = "/login";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [allowRender, setAllowRender] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) {
      const redirect = pathname || "/dashboard";
      router.replace(`${LOGIN_PATH}?redirect=${encodeURIComponent(redirect)}`);
      return;
    }
    setAllowRender(true);
  }, [router, pathname]);

  if (!allowRender) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-sky-500 border-t-transparent" />
      </div>
    );
  }
  return <>{children}</>;
}
