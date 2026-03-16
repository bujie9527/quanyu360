import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

type FilterToolbarProps = {
  title?: string;
  description?: string;
  children: ReactNode;
  className?: string;
};

export function FilterToolbar({ title, description, children, className }: FilterToolbarProps) {
  return (
    <div className={cn("rounded-2xl border border-slate-800 bg-slate-950/80 p-4", className)}>
      {(title || description) ? (
        <div className="mb-4">
          {title ? <p className="text-sm font-medium text-slate-100">{title}</p> : null}
          {description ? <p className="mt-1 text-sm text-slate-400">{description}</p> : null}
        </div>
      ) : null}
      <div className="flex flex-col gap-3 lg:flex-row lg:flex-wrap lg:items-center">{children}</div>
    </div>
  );
}
