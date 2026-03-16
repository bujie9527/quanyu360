"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bot, KeyRound, Loader2, Settings, Eye, EyeOff } from "lucide-react";
import { useEffect, useState } from "react";

import {
  DataCell,
  DataRow,
  DataTable,
  PageHero,
  PanelHeader,
  TableShell
} from "@/components/shared/admin-kit";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  listSystemSettings,
  updateSystemSetting,
  type SystemConfigItem
} from "@/lib/api-admin";
import { cn } from "@/lib/utils";

const CATEGORY_LABELS: Record<string, { icon: typeof Bot; title: string }> = {
  llm: { icon: Bot, title: "大语言模型与 API" },
  general: { icon: Settings, title: "常规配置" }
};

function EditConfigDialog({
  item,
  open,
  onOpenChange,
  onSaved
}: {
  item: SystemConfigItem | null;
  open: boolean;
  onOpenChange: (v: boolean) => void;
  onSaved: () => void;
}) {
  const queryClient = useQueryClient();
  const [value, setValue] = useState("");
  const [showSecret, setShowSecret] = useState(false);

  useEffect(() => {
    if (item && open) setValue("");
  }, [item, open]);

  const mutation = useMutation({
    mutationFn: (v: string) =>
      updateSystemSetting(item!.key, {
        value: v,
        is_secret: item!.is_secret
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-settings"] });
      onSaved();
      onOpenChange(false);
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!item) return;
    // For secrets: empty = keep existing, non-empty = update
    if (item.is_secret && !value.trim() && item.value_set) {
      onOpenChange(false);
      return;
    }
    mutation.mutate(value.trim());
  };

  if (!item) return null;

  const isSecret = item.is_secret;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <KeyRound className="h-5 w-5 text-amber-500" />
              编辑: {item.key}
            </DialogTitle>
            <DialogDescription>
              {item.description || "配置项"}
              {isSecret && (
                <span className="mt-1 block text-amber-600/90">
                  密钥已脱敏显示。输入新值以更新，留空则保持原值。
                </span>
              )}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="config-value">
                {isSecret ? "新值（留空保持）" : "值"}
              </Label>
              <div className="relative">
                <Input
                  id="config-value"
                  type={isSecret && !showSecret ? "password" : "text"}
                  placeholder={
                    isSecret && item.value_set
                      ? "输入新密钥替换，或留空保持不变"
                      : "输入配置值"
                  }
                  value={value}
                  onChange={(e) => setValue(e.target.value)}
                  className="font-mono text-sm"
                  autoComplete="off"
                />
                {isSecret && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-1 top-1/2 h-7 w-7 min-w-7 -translate-y-1/2 p-0"
                    onClick={() => setShowSecret((s) => !s)}
                  >
                    {showSecret ? (
                      <EyeOff className="h-4 w-4 text-slate-500" />
                    ) : (
                      <Eye className="h-4 w-4 text-slate-500" />
                    )}
                  </Button>
                )}
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              取消
            </Button>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              保存
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export default function SystemSettingsPage() {
  const queryClient = useQueryClient();
  const [categoryFilter, setCategoryFilter] = useState<string>("");
  const [editingItem, setEditingItem] = useState<SystemConfigItem | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  const settingsQuery = useQuery({
    queryKey: ["admin-settings", categoryFilter],
    queryFn: () => listSystemSettings(categoryFilter || undefined)
  });

  const items: SystemConfigItem[] = settingsQuery.data ?? [];

  const handleEdit = (item: SystemConfigItem) => {
    setEditingItem(item);
    setDialogOpen(true);
  };

  return (
    <div className="space-y-8">
      <PageHero
        eyebrow="系统设置"
        title="平台配置"
        description="管理环境变量、大语言模型 API Key 等系统级配置。"
      />

      <Card className="border-slate-700/60">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5 text-sky-400" />
            配置项
          </CardTitle>
          <CardDescription>
            按分类管理。密钥类配置以脱敏方式显示，编辑时可输入新值替换或留空保持。
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="mb-4 flex gap-2">
            <Button
              variant={categoryFilter === "" ? "default" : "outline"}
              size="sm"
              onClick={() => setCategoryFilter("")}
            >
              全部
            </Button>
            <Button
              variant={categoryFilter === "llm" ? "default" : "outline"}
              size="sm"
              onClick={() => setCategoryFilter("llm")}
            >
              LLM / API 密钥
            </Button>
            <Button
              variant={categoryFilter === "general" ? "default" : "outline"}
              size="sm"
              onClick={() => setCategoryFilter("general")}
            >
              常规
            </Button>
          </div>

          {settingsQuery.isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-sky-400" />
            </div>
          ) : items.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-700 bg-slate-900/40 py-12 text-center">
              <p className="text-sm text-slate-500">暂无配置项，请先运行数据库迁移。</p>
            </div>
          ) : (
            <TableShell>
              <DataTable
                headers={["键", "值", "分类", "类型", "说明", "操作"]}
              >
                {items.map((it) => {
                  const meta = CATEGORY_LABELS[it.category] ?? {
                    icon: Settings,
                    title: it.category
                  };
                  const Icon = meta.icon;
                  return (
                    <DataRow key={it.key}>
                      <DataCell className="font-mono text-sm">{it.key}</DataCell>
                      <DataCell className="max-w-[200px]">
                        <span
                          className={cn(
                            "truncate font-mono text-xs",
                            it.is_secret ? "text-slate-500" : "text-slate-300"
                          )}
                          title={it.is_secret ? "已脱敏" : it.value}
                        >
                          {it.is_secret
                            ? it.value_set
                              ? it.value
                              : "未设置"
                            : it.value || "—"}
                        </span>
                      </DataCell>
                      <DataCell>
                        <span className="flex items-center gap-1.5 text-slate-400">
                          <Icon className="h-4 w-4" />
                          {meta.title}
                        </span>
                      </DataCell>
                      <DataCell>
                        <span
                          className={cn(
                            "rounded px-2 py-0.5 text-xs",
                            it.is_secret
                              ? "bg-amber-500/15 text-amber-400"
                              : "bg-slate-700/50 text-slate-400"
                          )}
                        >
                          {it.is_secret ? "密钥" : "普通"}
                        </span>
                      </DataCell>
                      <DataCell className="max-w-[180px] truncate text-xs text-slate-500">
                        {it.description || "—"}
                      </DataCell>
                      <DataCell>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEdit(it)}
                        >
                          编辑
                        </Button>
                      </DataCell>
                    </DataRow>
                  );
                })}
              </DataTable>
            </TableShell>
          )}
        </CardContent>
      </Card>

      <EditConfigDialog
        item={editingItem}
        open={dialogOpen}
        onOpenChange={(v) => {
          setDialogOpen(v);
          if (!v) setEditingItem(null);
        }}
        onSaved={() => setEditingItem(null)}
      />
    </div>
  );
}
