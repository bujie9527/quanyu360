import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

type PageHeaderProps = {
  eyebrow?: string;
  title: string;
  description: string;
  children?: ReactNode;
  className?: string;
};

export function PageHeader({ eyebrow, title, description, children, className }: PageHeaderProps) {
  return (
    <section
      className={cn(
        "rounded-3xl border border-slate-800 bg-[linear-gradient(180deg,rgba(2,6,23,0.96)_0%,rgba(15,23,42,0.96)_100%)] p-6 shadow-sm",
        className
      )}
    >
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-4xl">
          {eyebrow ? <p className="text-sm font-medium text-sky-300">{eyebrow}</p> : null}
          <h3 className="mt-2 text-2xl font-semibold tracking-tight text-slate-100">{title}</h3>
          <p className="mt-3 text-sm leading-6 text-slate-400">{description}</p>
        </div>
        {children ? <div className="grid gap-3 sm:grid-cols-2">{children}</div> : null}
      </div>
    </section>
  );
}
