import type { ReactNode } from "react";

import { AuthGuard } from "@/components/auth/auth-guard";
import { Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";

export default function DashboardLayout({
  children
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <AuthGuard>
      <main className="min-h-screen bg-transparent">
        <div className="mx-auto flex min-h-screen">
          <Sidebar />
          <section className="flex-1 p-6 pt-20 md:p-8 md:pt-20">
            <Topbar />
            <div>{children}</div>
          </section>
        </div>
      </main>
    </AuthGuard>
  );
}
