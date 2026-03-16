import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

export function DataTable({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={cn("overflow-hidden rounded-2xl border border-slate-800 bg-slate-950/80", className)}>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-800">{children}</table>
      </div>
    </div>
  );
}

export function DataTableHeader({ children }: { children: ReactNode }) {
  return <thead className="bg-slate-900/80">{children}</thead>;
}

export function DataTableBody({ children }: { children: ReactNode }) {
  return <tbody className="divide-y divide-slate-800 bg-slate-950/80">{children}</tbody>;
}

export function DataTableRow({ children, className }: { children: ReactNode; className?: string }) {
  return <tr className={cn("transition-colors even:bg-slate-950 odd:bg-slate-950/70 hover:bg-slate-900", className)}>{children}</tr>;
}

export function DataTableHead({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <th className={cn("whitespace-nowrap px-4 py-3 text-left text-xs font-medium text-slate-500", className)}>
      {children}
    </th>
  );
}

export function DataTableCell({ children, className }: { children: ReactNode; className?: string }) {
  return <td className={cn("px-4 py-4 align-middle text-sm text-slate-300", className)}>{children}</td>;
}
