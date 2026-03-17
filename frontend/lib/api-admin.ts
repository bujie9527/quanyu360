import { getAuthHeaders } from "@/lib/auth";

const ADMIN_BASE =
  process.env.NEXT_PUBLIC_API_GATEWAY_URL ??
  process.env.NEXT_PUBLIC_PROJECT_SERVICE_URL ??
  "http://localhost:8300";

async function adminRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${ADMIN_BASE.replace(/\/$/, "")}/api/admin${path}`;
  const response = await fetch(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
      ...(init?.headers as Record<string, string>)
    },
    cache: "no-store"
  });
  if (!response.ok) {
    throw new Error(`Admin API error: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export type AdminDashboardData = {
  total_users: number;
  total_tenants: number;
  total_projects: number;
  total_agents: number;
  total_tasks: number;
  system_health: Record<string, string>;
};

export type TenantSummary = {
  id: string;
  name: string;
  slug: string;
  status: string;
  plan_name: string;
  created_at: string;
  updated_at: string;
};

export type TenantDetail = TenantSummary & {
  settings: Record<string, unknown>;
};

export type AdminUser = {
  id: string;
  email: string;
  full_name: string;
  tenant_id: string;
  role: string;
  status: string;
  created_at: string | null;
};

export async function getAdminDashboard(): Promise<AdminDashboardData> {
  return adminRequest<AdminDashboardData>("/dashboard");
}

export async function listAdminTenants(params?: {
  status?: string;
  search?: string;
  limit?: number;
  offset?: number;
}): Promise<{ items: TenantSummary[]; total: number }> {
  const qs = new URLSearchParams();
  if (params?.status) qs.set("status", params.status);
  if (params?.search) qs.set("search", params.search);
  if (params?.limit) qs.set("limit", String(params.limit));
  if (params?.offset) qs.set("offset", String(params.offset));
  const path = qs.toString() ? `/tenants?${qs}` : "/tenants";
  return adminRequest<{ items: TenantSummary[]; total: number }>(path);
}

export async function getTenantDetail(tenantId: string): Promise<TenantDetail> {
  return adminRequest<TenantDetail>(`/tenants/${tenantId}`);
}

export async function createTenant(payload: {
  name: string;
  slug: string;
  status?: string;
  plan_name?: string;
  settings?: Record<string, unknown>;
}): Promise<TenantDetail> {
  return adminRequest<TenantDetail>("/tenants", {
    method: "POST",
    body: JSON.stringify({
      name: payload.name,
      slug: payload.slug,
      status: payload.status ?? "active",
      plan_name: payload.plan_name ?? "mvp",
      settings: payload.settings ?? {}
    })
  });
}

export async function listAdminUsers(params?: {
  tenant_id?: string;
  limit?: number;
  offset?: number;
}): Promise<{ items: AdminUser[]; total: number }> {
  const qs = new URLSearchParams();
  if (params?.tenant_id) qs.set("tenant_id", params.tenant_id);
  if (params?.limit) qs.set("limit", String(params.limit));
  if (params?.offset) qs.set("offset", String(params.offset));
  const path = qs.toString() ? `/users?${qs}` : "/users";
  return adminRequest<{ items: AdminUser[]; total: number }>(path);
}

export async function listAdminProjects(params?: {
  limit?: number;
  offset?: number;
}): Promise<{ items: unknown[]; total: number }> {
  const qs = new URLSearchParams();
  if (params?.limit) qs.set("limit", String(params.limit));
  if (params?.offset) qs.set("offset", String(params.offset));
  const path = qs.toString() ? `/projects?${qs}` : "/projects";
  return adminRequest<{ items: unknown[]; total: number }>(path);
}

export async function listAdminAgents(params?: {
  limit?: number;
  offset?: number;
}): Promise<{ items: unknown[]; total: number }> {
  const qs = new URLSearchParams();
  if (params?.limit) qs.set("limit", String(params.limit));
  if (params?.offset) qs.set("offset", String(params.offset));
  const path = qs.toString() ? `/agents?${qs}` : "/agents";
  return adminRequest<{ items: unknown[]; total: number }>(path);
}

const API_BASE =
  process.env.NEXT_PUBLIC_API_GATEWAY_URL ??
  process.env.NEXT_PUBLIC_PROJECT_SERVICE_URL ??
  "http://localhost:8300";

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE.replace(/\/$/, "")}${path}`;
  const response = await fetch(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
      ...(init?.headers as Record<string, string>)
    },
    cache: "no-store"
  });
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export type AgentInstanceItem = {
  id: string;
  tenant_id: string;
  project_id: string;
  template_id: string | null;
  name: string;
  model: string;
  knowledge_base_id: string | null;
  template_name?: string;
  project_name?: string;
  knowledge_base_name?: string;
  created_at?: string;
};

export type AgentTemplateItem = {
  id: string;
  name: string;
  slug?: string;
  model: string;
  enabled?: boolean;
  description?: string | null;
  default_tools?: string[];
  default_workflows?: string[];
  system_prompt?: string;
  created_at?: string;
};

export async function listAgentInstances(params?: {
  project_id?: string;
  template_id?: string;
  enabled?: boolean;
  limit?: number;
  offset?: number;
}): Promise<{ items: AgentInstanceItem[]; total: number }> {
  const qs = new URLSearchParams();
  if (params?.project_id) qs.set("project_id", params.project_id);
  if (params?.template_id) qs.set("template_id", params.template_id);
  if (params?.enabled != null) qs.set("enabled", String(params.enabled));
  if (params?.limit) qs.set("limit", String(params.limit));
  if (params?.offset) qs.set("offset", String(params.offset));
  const path = qs.toString() ? `/api/agent/instances?${qs}` : "/api/agent/instances";
  return apiRequest<{ items: AgentInstanceItem[]; total: number }>(path);
}

export async function getAgentInstance(
  instanceId: string
): Promise<AgentInstanceItem & { description?: string; system_prompt?: string; enabled?: boolean }> {
  return apiRequest(`/api/agent/instances/${instanceId}`);
}

export async function updateAgentInstance(
  instanceId: string,
  payload: { knowledge_base_id?: string | null; name?: string; model?: string; enabled?: boolean }
): Promise<AgentInstanceItem> {
  const body: Record<string, unknown> = {};
  if (payload.knowledge_base_id !== undefined) body.knowledge_base_id = payload.knowledge_base_id || null;
  if (payload.name !== undefined) body.name = payload.name;
  if (payload.model !== undefined) body.model = payload.model;
  if (payload.enabled !== undefined) body.enabled = payload.enabled;
  return apiRequest(`/api/agent/instances/${instanceId}`, {
    method: "PUT",
    body: JSON.stringify(body)
  });
}

export type KnowledgeBaseItem = {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  project_id: string;
};

export async function listProjectKnowledgeBases(
  projectId: string
): Promise<KnowledgeBaseItem[]> {
  return apiRequest<KnowledgeBaseItem[]>(`/api/projects/${projectId}/knowledge-bases`);
}

export async function listAgentTemplates(params?: {
  enabled?: boolean;
  limit?: number;
  offset?: number;
}): Promise<{ items: AgentTemplateItem[]; total: number }> {
  const qs = new URLSearchParams();
  if (params?.enabled != null) qs.set("enabled", String(params.enabled));
  if (params?.limit) qs.set("limit", String(params.limit));
  if (params?.offset) qs.set("offset", String(params.offset));
  const path = qs.toString() ? `/api/agent/templates?${qs}` : "/api/agent/templates";
  return apiRequest<{ items: AgentTemplateItem[]; total: number }>(path);
}

export async function getAgentTemplate(templateId: string): Promise<AgentTemplateItem> {
  return apiRequest<AgentTemplateItem>(`/api/agent/templates/${templateId}`);
}

export async function createAgentTemplate(payload: {
  name: string;
  description?: string | null;
  system_prompt?: string;
  model?: string;
  default_tools?: string[];
  default_workflows?: string[];
  config_schema?: Record<string, unknown>;
  enabled?: boolean;
}): Promise<AgentTemplateItem> {
  return apiRequest<AgentTemplateItem>("/api/agent/templates", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateAgentTemplate(
  templateId: string,
  payload: {
    name?: string;
    description?: string | null;
    system_prompt?: string;
    model?: string;
    default_tools?: string[];
    default_workflows?: string[];
    config_schema?: Record<string, unknown>;
    enabled?: boolean;
  }
): Promise<AgentTemplateItem> {
  return apiRequest<AgentTemplateItem>(`/api/agent/templates/${templateId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function deleteAgentTemplate(templateId: string): Promise<void> {
  const url = `${API_BASE.replace(/\/$/, "")}/api/agent/templates/${templateId}`;
  const response = await fetch(url, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
    },
    cache: "no-store",
  });
  if (!response.ok) throw new Error(`API error: ${response.status}`);
}

export async function listAdminTasks(params?: {
  limit?: number;
  offset?: number;
}): Promise<{ items: unknown[]; total: number }> {
  const qs = new URLSearchParams();
  if (params?.limit) qs.set("limit", String(params.limit));
  if (params?.offset) qs.set("offset", String(params.offset));
  const path = qs.toString() ? `/tasks?${qs}` : "/tasks";
  return adminRequest<{ items: unknown[]; total: number }>(path);
}

export async function listAdminWorkflows(params?: {
  project_id?: string;
  limit?: number;
  offset?: number;
}): Promise<{ items: unknown[]; total: number }> {
  const qs = new URLSearchParams();
  if (params?.project_id) qs.set("project_id", params.project_id);
  if (params?.limit) qs.set("limit", String(params.limit));
  if (params?.offset) qs.set("offset", String(params.offset));
  const path = qs.toString() ? `/workflows?${qs}` : "/workflows";
  return adminRequest<{ items: unknown[]; total: number }>(path);
}

export type RoleSummary = {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
};

export type UserRoleAssignment = {
  id: string;
  user_id: string;
  role_id: string;
  tenant_id: string | null;
  created_at: string;
};

export async function listAdminRoles(params?: {
  limit?: number;
  offset?: number;
}): Promise<{ items: RoleSummary[]; total: number }> {
  const qs = new URLSearchParams();
  if (params?.limit) qs.set("limit", String(params.limit));
  if (params?.offset) qs.set("offset", String(params.offset));
  const path = qs.toString() ? `/roles?${qs}` : "/roles";
  return adminRequest<{ items: RoleSummary[]; total: number }>(path);
}

export async function getAdminRole(roleId: string): Promise<RoleSummary> {
  return adminRequest<RoleSummary>(`/roles/${roleId}`);
}

export async function createAdminRole(payload: {
  slug: string;
  name: string;
  description?: string | null;
}): Promise<RoleSummary> {
  return adminRequest<RoleSummary>("/roles", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function updateAdminRole(
  roleId: string,
  payload: { slug?: string; name?: string; description?: string | null }
): Promise<RoleSummary> {
  return adminRequest<RoleSummary>(`/roles/${roleId}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export async function deleteAdminRole(roleId: string): Promise<void> {
  await adminRequest<void>(`/roles/${roleId}`, { method: "DELETE" });
}

export async function getUserRoles(userId: string): Promise<UserRoleAssignment[]> {
  return adminRequest<UserRoleAssignment[]>(`/users/${userId}/roles`);
}

export async function assignRolesToUser(
  userId: string,
  payload: { roles: Array<{ role_id: string; tenant_id?: string | null }> }
): Promise<UserRoleAssignment[]> {
  return adminRequest<UserRoleAssignment[]>(`/users/${userId}/roles`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function unassignRoleFromUser(
  userId: string,
  params: { role_id: string; tenant_id?: string | null }
): Promise<void> {
  const qs = new URLSearchParams();
  qs.set("role_id", params.role_id);
  if (params.tenant_id != null) qs.set("tenant_id", params.tenant_id);
  await adminRequest<void>(`/users/${userId}/roles?${qs}`, { method: "DELETE" });
}

export type UsageLogEntry = {
  id: string;
  tenant_id: string;
  usage_type: string;
  project_id: string | null;
  prompt_tokens: number;
  completion_tokens: number;
  quantity: number;
  created_at: string;
};

export type UsageSummary = {
  tenant_id: string;
  llm_tokens_total: number;
  llm_prompt_tokens: number;
  llm_completion_tokens: number;
  workflow_runs: number;
  tool_executions: number;
  from_at: string | null;
  to_at: string | null;
};

export type QuotaResource = {
  current: number;
  limit: number;
  allowed: boolean;
};

export type QuotaList = {
  tenant_id: string;
  quotas: Record<string, QuotaResource>;
};

export async function getUsageSummary(params: {
  tenant_id: string;
  from_at?: string;
  to_at?: string;
}): Promise<UsageSummary> {
  const qs = new URLSearchParams();
  qs.set("tenant_id", params.tenant_id);
  if (params.from_at) qs.set("from_at", params.from_at);
  if (params.to_at) qs.set("to_at", params.to_at);
  return adminRequest<UsageSummary>(`/usage/summary?${qs}`);
}

export async function listUsageLogs(params?: {
  tenant_id?: string;
  from_at?: string;
  to_at?: string;
  usage_type?: string;
  limit?: number;
  offset?: number;
}): Promise<{ items: UsageLogEntry[]; total: number }> {
  const qs = new URLSearchParams();
  if (params?.tenant_id) qs.set("tenant_id", params.tenant_id);
  if (params?.from_at) qs.set("from_at", params.from_at);
  if (params?.to_at) qs.set("to_at", params.to_at);
  if (params?.usage_type) qs.set("usage_type", params.usage_type);
  if (params?.limit) qs.set("limit", String(params.limit));
  if (params?.offset) qs.set("offset", String(params.offset));
  const path = qs.toString() ? `/usage?${qs}` : "/usage";
  return adminRequest<{ items: UsageLogEntry[]; total: number }>(path);
}

export async function getQuotas(tenantId: string): Promise<QuotaList> {
  return adminRequest<QuotaList>(`/quotas?tenant_id=${tenantId}`);
}

export async function updateTenantQuotas(
  tenantId: string,
  payload: {
    tasks_per_month?: number;
    llm_requests_per_month?: number;
    workflows_per_month?: number;
    wordpress_sites_per_month?: number;
  }
): Promise<QuotaList> {
  return adminRequest<QuotaList>(`/tenants/${tenantId}/quotas`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export async function getAdminUser(userId: string): Promise<AdminUser> {
  return adminRequest<AdminUser>(`/users/${userId}`);
}

export async function updateTenant(
  tenantId: string,
  payload: {
    name?: string;
    slug?: string;
    status?: string;
    plan_name?: string;
    settings?: Record<string, unknown>;
  }
): Promise<TenantDetail> {
  return adminRequest<TenantDetail>(`/tenants/${tenantId}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export async function deleteTenant(tenantId: string): Promise<void> {
  await adminRequest<void>(`/tenants/${tenantId}`, { method: "DELETE" });
}

export type PlatformDomainItem = {
  id: string;
  domain: string;
  api_base_url: string;
  server_id?: string | null;
  ssl_enabled: boolean;
  status: string;
  created_at: string;
  updated_at: string;
};

export async function listPlatformDomains(params?: {
  status?: string;
  limit?: number;
  offset?: number;
}): Promise<{ items: PlatformDomainItem[]; total: number }> {
  const qs = new URLSearchParams();
  if (params?.status) qs.set("status", params.status);
  if (params?.limit) qs.set("limit", String(params.limit));
  if (params?.offset) qs.set("offset", String(params.offset));
  const path = qs.toString() ? `/platform_domains?${qs}` : "/platform_domains";
  return adminRequest<{ items: PlatformDomainItem[]; total: number }>(path);
}

export async function createPlatformDomain(payload: {
  domain: string;
  api_base_url: string;
  server_id?: string | null;
  ssl_enabled?: boolean;
  status?: string;
}): Promise<PlatformDomainItem> {
  return adminRequest<PlatformDomainItem>("/platform_domains", {
    method: "POST",
    body: JSON.stringify({
      domain: payload.domain,
      api_base_url: payload.api_base_url,
      server_id: payload.server_id ?? null,
      ssl_enabled: payload.ssl_enabled ?? true,
      status: payload.status ?? "available"
    })
  });
}

export async function updatePlatformDomain(
  domainId: string,
  payload: { domain?: string; api_base_url?: string; server_id?: string | null; ssl_enabled?: boolean; status?: string }
): Promise<PlatformDomainItem> {
  return adminRequest<PlatformDomainItem>(`/platform_domains/${domainId}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export type ServerItem = {
  id: string;
  name: string;
  host: string;
  port: number;
  ssh_user: string;
  web_root: string;
  php_bin: string;
  wp_cli_bin: string;
  mysql_host: string;
  mysql_port: number;
  mysql_admin_user: string;
  mysql_db_prefix: string;
  status: "active" | "inactive";
  created_at: string;
  updated_at: string;
};

export async function listServers(params?: {
  status?: "active" | "inactive";
  limit?: number;
  offset?: number;
}): Promise<{ items: ServerItem[]; total: number }> {
  const qs = new URLSearchParams();
  if (params?.status) qs.set("status", params.status);
  if (params?.limit) qs.set("limit", String(params.limit));
  if (params?.offset) qs.set("offset", String(params.offset));
  const path = qs.toString() ? `/servers?${qs}` : "/servers";
  return adminRequest<{ items: ServerItem[]; total: number }>(path);
}

export async function createServer(payload: {
  name: string;
  host: string;
  port?: number;
  ssh_user: string;
  ssh_password?: string | null;
  ssh_private_key?: string | null;
  web_root: string;
  php_bin?: string;
  wp_cli_bin?: string;
  mysql_host?: string;
  mysql_port?: number;
  mysql_admin_user: string;
  mysql_admin_password: string;
  mysql_db_prefix?: string;
  status?: "active" | "inactive";
}): Promise<ServerItem> {
  return adminRequest<ServerItem>("/servers", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateServer(
  serverId: string,
  payload: Partial<{
    name: string;
    host: string;
    port: number;
    ssh_user: string;
    ssh_password: string | null;
    ssh_private_key: string | null;
    web_root: string;
    php_bin: string;
    wp_cli_bin: string;
    mysql_host: string;
    mysql_port: number;
    mysql_admin_user: string;
    mysql_admin_password: string;
    mysql_db_prefix: string;
    status: "active" | "inactive";
  }>
): Promise<ServerItem> {
  return adminRequest<ServerItem>(`/servers/${serverId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function deleteServer(serverId: string): Promise<void> {
  await adminRequest<void>(`/servers/${serverId}`, { method: "DELETE" });
}

export async function testServer(serverId: string): Promise<{ success: boolean; message: string }> {
  return adminRequest<{ success: boolean; message: string }>(`/servers/${serverId}/test`, { method: "POST" });
}

export async function deletePlatformDomain(domainId: string): Promise<void> {
  await adminRequest<void>(`/platform_domains/${domainId}`, { method: "DELETE" });
}

export type AuditLogEntry = {
  id: string;
  tenant_id: string;
  project_id: string | null;
  actor_user_id: string | null;
  action: string;
  entity_type: string;
  entity_id: string | null;
  correlation_id: string | null;
  created_at: string;
  payload: Record<string, unknown>;
};

export type SystemConfigItem = {
  key: string;
  value: string;
  value_set: boolean;
  category: string;
  is_secret: boolean;
  description: string | null;
  updated_at: string | null;
};

export async function listSystemSettings(category?: string): Promise<SystemConfigItem[]> {
  const qs = category ? `?category=${encodeURIComponent(category)}` : "";
  return adminRequest<SystemConfigItem[]>(`/settings${qs}`);
}

export async function getSystemSetting(key: string): Promise<SystemConfigItem> {
  return adminRequest<SystemConfigItem>(`/settings/${encodeURIComponent(key)}`);
}

export async function updateSystemSetting(
  key: string,
  payload: { value: string; category?: string; is_secret?: boolean; description?: string | null }
): Promise<SystemConfigItem> {
  return adminRequest<SystemConfigItem>(`/settings/${encodeURIComponent(key)}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export async function listAdminAuditLogs(params?: {
  tenant_id?: string;
  entity_type?: string;
  action?: string;
  correlation_id?: string;
  since?: string;
  until?: string;
  limit?: number;
  offset?: number;
}): Promise<{ items: AuditLogEntry[]; total: number }> {
  const qs = new URLSearchParams();
  if (params?.tenant_id) qs.set("tenant_id", params.tenant_id);
  if (params?.entity_type) qs.set("entity_type", params.entity_type);
  if (params?.action) qs.set("action", params.action);
  if (params?.correlation_id) qs.set("correlation_id", params.correlation_id);
  if (params?.since) qs.set("since", params.since);
  if (params?.until) qs.set("until", params.until);
  if (params?.limit) qs.set("limit", String(params.limit));
  if (params?.offset) qs.set("offset", String(params.offset));
  const path = qs.toString() ? `/audit?${qs}` : "/audit";
  return adminRequest<{ items: AuditLogEntry[]; total: number }>(path);
}

export type SitePoolSiteItem = {
  id: string;
  domain: string;
  name: string;
  api_url: string;
  status: "active" | "inactive" | "error";
  pool_status: "ready" | "installing" | "assigned" | "error";
  platform_domain_id: string | null;
  server_id: string | null;
  install_task_run_id: string | null;
  tenant_id: string | null;
  project_id: string | null;
  created_at: string;
  updated_at: string;
};

export type InstallWorkflowItem = {
  id: string;
  project_id: string;
  name: string;
  slug: string;
  status: string;
};

export type SiteInstallStepLog = {
  id: string;
  step_name: string;
  status: string;
  duration: number;
  output_json: Record<string, unknown>;
  created_at: string;
};

export type SiteInstallRun = {
  task_run_id: string;
  status: string;
  start_time: string;
  end_time: string | null;
  steps: SiteInstallStepLog[];
};

export async function listSitePoolSites(params?: {
  server_id?: string;
  assigned?: boolean;
  status?: "active" | "inactive" | "error";
  limit?: number;
  offset?: number;
}): Promise<{ items: SitePoolSiteItem[]; total: number }> {
  const qs = new URLSearchParams();
  if (params?.server_id) qs.set("server_id", params.server_id);
  if (params?.assigned !== undefined) qs.set("assigned", String(params.assigned));
  if (params?.status) qs.set("status", params.status);
  if (params?.limit) qs.set("limit", String(params.limit));
  if (params?.offset) qs.set("offset", String(params.offset));
  const path = qs.toString() ? `/site-pool/sites?${qs}` : "/site-pool/sites";
  return adminRequest<{ items: SitePoolSiteItem[]; total: number }>(path);
}

export async function listInstallWorkflows(): Promise<{ items: InstallWorkflowItem[]; total: number }> {
  return adminRequest<{ items: InstallWorkflowItem[]; total: number }>("/site-pool/install-workflows");
}

export async function batchInstallSites(payload: {
  server_id: string;
  domain_ids: string[];
  workflow_id?: string;
  admin_username: string;
  admin_password: string;
  admin_email: string;
  site_title_prefix?: string;
}): Promise<{ site_ids: string[]; task_run_ids: string[] }> {
  return adminRequest<{ site_ids: string[]; task_run_ids: string[] }>("/site-pool/batch-install", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function assignSiteToTenant(
  siteId: string,
  payload: { tenant_id: string; project_id: string }
): Promise<SitePoolSiteItem> {
  return adminRequest<SitePoolSiteItem>(`/site-pool/sites/${siteId}/assign`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function getSiteInstallRun(siteId: string): Promise<SiteInstallRun | null> {
  return adminRequest<SiteInstallRun | null>(`/site-pool/sites/${siteId}/install-run`);
}
