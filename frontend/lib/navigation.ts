import {
  Activity,
  BarChart3,
  Bot,
  BriefcaseBusiness,
  FileText,
  BookOpen,
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
  Users
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
  {
    href: "/dashboard",
    label: "工作台",
    description: "平台总览与运营指标",
    icon: LayoutDashboard
  },
  {
    href: "/analytics",
    label: "数据分析",
    description: "任务执行、Agent 性能与系统使用",
    icon: BarChart3
  },
  {
    href: "/projects",
    label: "项目空间",
    description: "项目、团队与归属管理",
    icon: BriefcaseBusiness
  },
  {
    href: "/agents",
    label: "智能员工",
    description: "Agent、模型与工具权限",
    icon: Bot
  },
  {
    href: "/tasks",
    label: "任务中心",
    description: "任务队列与执行状态",
    icon: ListTodo
  },
  {
    href: "/workflow-builder",
    label: "流程编排",
    description: "步骤配置与自动化链路",
    icon: GitBranchPlus
  },
  {
    type: "group",
    label: "矩阵建站",
    icon: Globe,
    children: [
      {
        href: "/matrix-planner",
        label: "站点规划",
        description: "目标人群与多站点规划",
        icon: Bot
      },
      {
        href: "/site-building",
        label: "建站任务",
        description: "WordPress 自动建站与执行",
        icon: Globe
      },
      {
        href: "/matrix-sites",
        label: "站点管理",
        description: "矩阵站点状态与进度",
        icon: Activity
      }
    ]
  },
  {
    href: "/results",
    label: "执行结果",
    description: "运行日志与输出详情",
    icon: ScrollText
  }
];

export const adminNavigationItems = [
  {
    href: "/admin",
    label: "管理概览",
    description: "平台统计与系统健康",
    icon: Shield
  },
  {
    href: "/admin/tenants",
    label: "租户管理",
    description: "查看与创建租户",
    icon: BriefcaseBusiness
  },
  {
    href: "/admin/users",
    label: "用户管理",
    description: "跨租户查看用户",
    icon: Users
  },
  {
    href: "/admin/roles",
    label: "角色管理",
    description: "RBAC 角色",
    icon: KeyRound
  },
  {
    href: "/admin/projects",
    label: "项目管理",
    description: "跨租户查看项目",
    icon: Activity
  },
  {
    type: "group",
    label: "AI员工",
    icon: Bot,
    children: [
      { href: "/admin/agent-templates", label: "Agent Templates", description: "Agent 模板", icon: FileText },
      { href: "/admin/agents", label: "Agents", description: "Agent 实例", icon: Bot },
      { href: "/admin/knowledge-base", label: "KnowledgeBase", description: "知识库", icon: BookOpen },
      { href: "/admin/agent-logs", label: "Agent Logs", description: "Agent 执行日志", icon: ScrollText }
    ]
  },
  {
    href: "/admin/tasks",
    label: "任务管理",
    description: "跨项目查看任务",
    icon: ListTodo
  },
  {
    href: "/admin/workflows",
    label: "流程管理",
    description: "跨项目查看工作流",
    icon: GitBranchPlus
  },
  {
    href: "/admin/audit",
    label: "审计日志",
    description: "Agent 行为、工具调用与流程执行",
    icon: ShieldCheck
  },
  {
    href: "/admin/usage",
    label: "用量与配额",
    description: "租户用量与配额",
    icon: BarChart3
  },
  {
    href: "/admin/platform-domains",
    label: "域名管理",
    description: "建站平台域名库",
    icon: Globe
  },
  {
    href: "/admin/servers",
    label: "服务器管理",
    description: "SSH/WP-CLI 服务器配置",
    icon: Server
  },
  {
    href: "/admin/settings",
    label: "系统设置",
    description: "平台配置",
    icon: Settings
  }
];

export const pageMeta: Record<string, { title: string; subtitle: string }> = {
  "/dashboard": {
    title: "运营工作台",
    subtitle: "集中查看项目进展、Agent 状态、任务队列与系统健康度。"
  },
  "/analytics": {
    title: "数据分析",
    subtitle: "任务执行、Agent 性能与系统使用情况的可视化分析。"
  },
  "/projects": {
    title: "项目空间",
    subtitle: "创建业务项目，管理负责人、成员分工与资源覆盖情况。"
  },
  "/agents": {
    title: "智能员工",
    subtitle: "管理 AI 员工、模型配置、提示词与工具调用权限。"
  },
  "/tasks": {
    title: "任务中心",
    subtitle: "发起任务、推进执行，并跟踪队列、重试和分配状态。"
  },
  "/workflow-builder": {
    title: "流程编排",
    subtitle: "设计多步骤自动化流程，并关联 Agent 与工具执行链路。"
  },
  "/site-building": {
    title: "建站任务",
    subtitle: "WordPress 自动建站，选择项目与域名批量创建。"
  },
  "/matrix-planner": {
    title: "站点规划",
    subtitle: "使用矩阵站规划 Agent 生成多站点内容方案并审核。"
  },
  "/matrix-sites": {
    title: "站点管理",
    subtitle: "查看矩阵站点状态、执行进度与规划映射关系。"
  },
  "/results": {
    title: "执行结果",
    subtitle: "查看工作流执行状态、步骤轨迹、上下文日志与输出结果。"
  },
  "/admin": {
    title: "管理概览",
    subtitle: "平台统计、系统健康与管理总览。"
  },
  "/admin/tenants": {
    title: "租户管理",
    subtitle: "创建与管理平台租户。"
  },
  "/admin/users": {
    title: "用户管理",
    subtitle: "跨租户查看与管理用户。"
  },
  "/admin/roles": {
    title: "角色管理",
    subtitle: "RBAC 角色创建与管理。"
  },
  "/admin/workflows": {
    title: "流程管理",
    subtitle: "跨项目查看所有工作流。"
  },
  "/admin/usage": {
    title: "用量与配额",
    subtitle: "租户用量统计与配额管理。"
  },
  "/admin/platform-domains": {
    title: "域名管理",
    subtitle: "平台建站域名库，供租户建站选用。"
  },
  "/admin/servers": {
    title: "服务器管理",
    subtitle: "管理建站服务器连接信息与连通性测试。"
  },
  "/admin/settings": {
    title: "系统设置",
    subtitle: "平台配置与偏好设置。"
  },
  "/admin/projects": {
    title: "项目管理",
    subtitle: "跨租户查看所有项目。"
  },
  "/admin/tasks": {
    title: "任务管理",
    subtitle: "跨项目查看所有任务。"
  },
  "/admin/audit": {
    title: "审计日志",
    subtitle: "Agent 执行、工具调用与流程执行审计记录。"
  },
  "/admin/agent-templates": {
    title: "Agent Templates",
    subtitle: "Agent 模板管理。"
  },
  "/admin/agents": {
    title: "Agents",
    subtitle: "Agent 实例列表，含 template、project、model、knowledge_base。"
  },
  "/admin/knowledge-base": {
    title: "KnowledgeBase",
    subtitle: "知识库管理。"
  },
  "/admin/agent-logs": {
    title: "Agent Logs",
    subtitle: "Agent 执行日志。"
  }
};
