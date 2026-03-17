import {
  Activity,
  BarChart3,
  BookOpen,
  Bot,
  BriefcaseBusiness,
  FileText,
  GitBranchPlus,
  Globe,
  KeyRound,
  LayoutDashboard,
  ListTodo,
  ScrollText,
  Server,
  Settings,
  Shield,
  ShieldCheck,
  Users,
  Wrench,
} from "lucide-react";

export type NavLink = {
  href: string;
  label: string;
  description: string;
  icon: typeof Bot;
};

export type NavGroup = {
  type: "group";
  label: string;
  icon: typeof Bot;
  children: NavLink[];
};

export const navigationItems = [
  { href: "/dashboard", label: "工作台", description: "平台总览", icon: LayoutDashboard },
  { href: "/analytics", label: "数据分析", description: "执行与使用分析", icon: BarChart3 },
  { href: "/projects", label: "项目空间", description: "项目与成员管理", icon: BriefcaseBusiness },
  { href: "/agents", label: "智能员工", description: "Agent 管理", icon: Bot },
  { href: "/tasks", label: "任务中心", description: "任务队列与状态", icon: ListTodo },
  { href: "/workflow-builder", label: "流程编排", description: "自动化链路", icon: GitBranchPlus },
  {
    type: "group",
    label: "矩阵建站",
    icon: Globe,
    children: [
      { href: "/matrix-planner", label: "站点规划", description: "多站点规划", icon: Bot },
      { href: "/site-building", label: "建站任务", description: "批量建站执行", icon: Globe },
      { href: "/matrix-sites", label: "站点管理", description: "站点总览与进度", icon: Activity },
    ],
  },
  { href: "/results", label: "执行结果", description: "运行日志与输出", icon: ScrollText },
];

export const adminNavigationItems = [
  { href: "/admin", label: "管理概览", description: "平台健康与统计", icon: Shield },
  { href: "/admin/tenants", label: "租户管理", description: "查看与创建租户", icon: BriefcaseBusiness },
  { href: "/admin/users", label: "用户管理", description: "跨租户用户", icon: Users },
  { href: "/admin/roles", label: "角色管理", description: "RBAC 角色", icon: KeyRound },
  { href: "/admin/projects", label: "项目管理", description: "跨租户项目", icon: Activity },
  {
    type: "group",
    label: "AI员工",
    icon: Bot,
    children: [
      { href: "/admin/agent-templates", label: "Agent Templates", description: "模板管理", icon: FileText },
      { href: "/admin/agents", label: "Agents", description: "实例管理", icon: Bot },
      { href: "/admin/knowledge-base", label: "KnowledgeBase", description: "知识库", icon: BookOpen },
      { href: "/admin/agent-logs", label: "Agent Logs", description: "执行日志", icon: ScrollText },
    ],
  },
  { href: "/admin/tasks", label: "任务管理", description: "跨项目任务", icon: ListTodo },
  { href: "/admin/workflows", label: "流程管理", description: "跨项目流程", icon: GitBranchPlus },
  { href: "/admin/audit", label: "审计日志", description: "行为审计", icon: ShieldCheck },
  { href: "/admin/usage", label: "用量与配额", description: "租户配额", icon: BarChart3 },
  {
    type: "group",
    label: "建站中心",
    icon: Globe,
    children: [
      { href: "/admin/platform-domains", label: "域名库", description: "批量域名管理", icon: Globe },
      { href: "/admin/servers", label: "服务器", description: "批量服务器管理", icon: Server },
      { href: "/admin/site-install", label: "批量建站", description: "批量安装 WordPress", icon: Wrench },
      { href: "/admin/site-pool", label: "站点库", description: "站点授权与绑定", icon: Activity },
    ],
  },
  { href: "/admin/settings", label: "系统设置", description: "平台配置", icon: Settings },
];

export const pageMeta: Record<string, { title: string; subtitle: string }> = {
  "/dashboard": { title: "运营工作台", subtitle: "项目、任务和系统健康总览。" },
  "/analytics": { title: "数据分析", subtitle: "任务执行与系统使用可视化。" },
  "/projects": { title: "项目空间", subtitle: "创建与管理业务项目。" },
  "/agents": { title: "智能员工", subtitle: "管理 Agent、模型与权限。" },
  "/tasks": { title: "任务中心", subtitle: "任务执行、重试和队列状态。" },
  "/workflow-builder": { title: "流程编排", subtitle: "设计多步骤自动化流程。" },
  "/site-building": { title: "建站任务", subtitle: "WordPress 自动建站执行。" },
  "/matrix-planner": { title: "站点规划", subtitle: "矩阵站点规划与审核。" },
  "/matrix-sites": { title: "站点管理", subtitle: "矩阵站点状态与执行进度。" },
  "/results": { title: "执行结果", subtitle: "运行日志与输出详情。" },
  "/admin": { title: "管理概览", subtitle: "平台管理总览。" },
  "/admin/tenants": { title: "租户管理", subtitle: "创建与管理平台租户。" },
  "/admin/users": { title: "用户管理", subtitle: "跨租户用户管理。" },
  "/admin/roles": { title: "角色管理", subtitle: "RBAC 角色维护。" },
  "/admin/projects": { title: "项目管理", subtitle: "跨租户项目视图。" },
  "/admin/tasks": { title: "任务管理", subtitle: "跨项目任务视图。" },
  "/admin/workflows": { title: "流程管理", subtitle: "跨项目工作流视图。" },
  "/admin/usage": { title: "用量与配额", subtitle: "租户用量统计与配额管理。" },
  "/admin/audit": { title: "审计日志", subtitle: "执行与调用审计记录。" },
  "/admin/platform-domains": { title: "域名库", subtitle: "平台可用域名池管理。" },
  "/admin/servers": { title: "服务器", subtitle: "建站服务器连接与状态管理。" },
  "/admin/site-install": { title: "批量建站", subtitle: "批量安装 WordPress 并查看实时日志。" },
  "/admin/site-pool": { title: "站点库", subtitle: "预建站点授权给租户并绑定项目。" },
  "/admin/settings": { title: "系统设置", subtitle: "平台配置项管理。" },
  "/admin/agent-templates": { title: "Agent Templates", subtitle: "Agent 模板管理。" },
  "/admin/agents": { title: "Agents", subtitle: "Agent 实例管理。" },
  "/admin/knowledge-base": { title: "KnowledgeBase", subtitle: "知识库管理。" },
  "/admin/agent-logs": { title: "Agent Logs", subtitle: "Agent 执行日志。" },
};
