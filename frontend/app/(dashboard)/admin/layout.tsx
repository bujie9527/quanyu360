import type { ReactNode } from "react";

export default function AdminLayout({
  children,
}: Readonly<{ children: ReactNode }>) {
  return (
    <div className="admin-layout relative min-h-full">
      <div className="absolute inset-y-0 left-0 w-1 rounded-r-full bg-gradient-to-b from-violet-500/60 via-sky-500/40 to-violet-500/60" aria-hidden />
      <div className="relative pl-6">{children}</div>
    </div>
  );
}
