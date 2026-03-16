"use client";

import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export const selectClassName =
  "saas-select";

type PageHeroProps = {
  eyebrow: string;
  title: string;
  description: string;
  children?: ReactNode;
};

export function PageHero({ eyebrow, title, description, children }: PageHeroProps) {
  return (
    <section className="overflow-hidden rounded-3xl border border-slate-800 bg-[linear-gradient(135deg,rgba(2,6,23,0.96)_0%,rgba(15,23,42,0.96)_55%,rgba(30,41,59,0.92)_100%)] p-6 shadow-sm">
      <div className="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
        <div className="max-w-3xl">
          <p className="text-sm font-medium text-sky-300">{eyebrow}</p>
          <h3 className="mt-2 text-2xl font-semibold tracking-tight text-slate-100">{title}</h3>
          <p className="mt-3 text-sm leading-6 text-slate-400">{description}</p>
        </div>
        {children ? <div className="grid gap-3 sm:grid-cols-2">{children}</div> : null}
      </div>
    </section>
  );
}

type HeroTipProps = {
  label: string;
  value: string;
};

export function HeroTip({ label, value }: HeroTipProps) {
  return (
    <div className="rounded-2xl border border-slate-700 bg-slate-900/80 px-4 py-3 shadow-sm transition-colors hover:border-slate-600 hover:bg-slate-900">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-2 text-sm font-medium leading-6 text-slate-200">{value}</p>
    </div>
  );
}

type MetricCardProps = {
  label: string;
  value: string;
  hint?: string;
  icon?: LucideIcon;
};

export function MetricCard({ label, value, hint, icon: Icon }: MetricCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-3">
        <div>
          <CardDescription>{label}</CardDescription>
          <CardTitle className="mt-2 text-3xl">{value}</CardTitle>
        </div>
        {Icon ? (
          <div className="rounded-xl border border-sky-500/20 bg-sky-500/10 p-3">
            <Icon className="h-5 w-5 text-sky-300" />
          </div>
        ) : null}
      </CardHeader>
      {hint ? (
        <CardContent>
          <p className="text-sm text-slate-400">{hint}</p>
        </CardContent>
      ) : null}
    </Card>
  );
}

type FilterBarProps = {
  title: string;
  description: string;
  children: ReactNode;
};

export function FilterBar({ title, description, children }: FilterBarProps) {
  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-950/80 p-4 shadow-sm">
      <div className="mb-4">
        <p className="text-sm font-medium text-slate-100">{title}</p>
        <p className="mt-1 text-sm text-slate-400">{description}</p>
      </div>
      <div className="flex flex-col gap-3 lg:flex-row lg:flex-wrap lg:items-center">{children}</div>
    </section>
  );
}

type PanelHeaderProps = {
  title: string;
  description: string;
  action?: ReactNode;
};

export function PanelHeader({ title, description, action }: PanelHeaderProps) {
  return (
    <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h3 className="text-lg font-semibold text-slate-100">{title}</h3>
        <p className="mt-1 text-sm text-slate-400">{description}</p>
      </div>
      {action}
    </div>
  );
}

type TableShellProps = {
  children: ReactNode;
  className?: string;
};

export function TableShell({ children, className }: TableShellProps) {
  return <div className={cn("overflow-hidden rounded-2xl border border-slate-800 bg-slate-950/80 shadow-sm", className)}>{children}</div>;
}

type TableProps = {
  headers: string[];
  children: ReactNode;
};

export function DataTable({ headers, children }: TableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full border-separate border-spacing-0">
        <thead>
          <tr className="bg-slate-900/80">
            {headers.map((header) => (
              <th key={header} className="border-b border-slate-800 px-4 py-3 text-left text-xs font-medium text-slate-400">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}

type DataRowProps = {
  children: ReactNode;
  selected?: boolean;
  onClick?: () => void;
};

export function DataRow({ children, selected = false, onClick }: DataRowProps) {
  return (
    <tr
      className={cn(
        "border-b border-slate-800 text-sm text-slate-300 transition-colors even:bg-slate-950 odd:bg-slate-950/70",
        selected
          ? "bg-sky-500/12 shadow-[inset_3px_0_0_0_rgba(56,189,248,0.9)]"
          : "hover:bg-slate-900 hover:shadow-[inset_3px_0_0_0_rgba(71,85,105,0.55)] active:bg-slate-800/90",
        onClick ? "cursor-pointer" : ""
      )}
      onClick={onClick}
    >
      {children}
    </tr>
  );
}

type DataCellProps = {
  children: ReactNode;
  className?: string;
};

export function DataCell({ children, className }: DataCellProps) {
  return <td className={cn("border-b border-slate-800 px-4 py-4 align-top", className)}>{children}</td>;
}
