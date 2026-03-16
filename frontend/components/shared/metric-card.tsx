import type { LucideIcon } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";

type MetricCardProps = {
  title: string;
  value: string | number;
  description?: string;
  icon?: LucideIcon;
};

export function MetricCard({ title, value, description, icon: Icon }: MetricCardProps) {
  return (
    <Card className="rounded-2xl border-slate-800 shadow-none">
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm text-slate-400">{title}</p>
            <p className="mt-3 text-3xl font-semibold tracking-tight text-slate-100">{value}</p>
          </div>
          {Icon ? (
            <div className="rounded-2xl border border-sky-500/20 bg-sky-500/10 p-3">
              <Icon className="h-5 w-5 text-sky-300" />
            </div>
          ) : null}
        </div>
        {description ? <p className="mt-4 text-sm text-slate-400">{description}</p> : null}
      </CardContent>
    </Card>
  );
}
