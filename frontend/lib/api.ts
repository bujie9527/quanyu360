import { clearToken, getAuthHeaders } from "@/lib/auth";

export type ServiceHealth = {
  status: string;
  service: string;
  timestamp: string;
};

export type PlatformService = {
  name: string;
  url: string;
  domain: string;
};

export type ProjectRecord = {
  id: string;
  tenant_id: string;
  key: string;
  name: string;
  description: string | null;
  owner_id: string | null;
  status: string;
  project_type: "general" | "matrix_site";
  matrix_config: Record<string, unknown>;
  team_members: Array<{
    user_id: string;
    email: string;
    full_name: string;
    role: string;
  }>;
  agent_count: number;
  task_count: number;
  workflow_count: number;
  created_at: string;
  updated_at: string;
};

export type AgentRecord = {
  id: string;
  project_id: string;
  name: string;
  slug: string;
  role: string;
  role_title: string;
  model: string;
  status: string;
  system_prompt?: string;
  max_concurrency?: number;
  tool_count?: number;
  workflow_count?: number;
  skill_count?: number;
};

export type TaskRecord = {
  id: string;
  title: string;
  description: string | null;
  status: string;
  priority: string;
  project_id: string;
  agent_id: string | null;
  workflow_id: string | null;
  attempt_count: number;
  max_attempts: number;
  due_at: string | null;
  created_at: string;
  updated_at: string;
};

export type TaskDetailRecord = TaskRecord & {
  output_payload?: Record<string, unknown>;
  input_payload?: Record<string, unknown>;
  last_error?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
};

export type WorkflowStepRecord = {
  id: string;
  workflow_id: string;
  step_key: string;
  name: string;
  type: string;
  config: Record<string, unknown>;
  next_step: string | null;
  sequence: number;
  retry_limit: number;
  timeout_seconds: number;
  assigned_agent_id: string | null;
  tool_id: string | null;
};

export type WorkflowRecord = {
  id: string;
  project_id: string;
  name: string;
  slug: string;
  version: number;
  status: string;
  trigger_type: string;
  definition?: Record<string, unknown>;
  step_count?: number;
  steps?: WorkflowStepRecord[];
  created_at: string;
  updated_at: string;
};

export type ExecutionSummary = {
  execution_id: string;
  workflow_id: string;
  status: string;
  current_step: string | null;
  started_at: string;
  completed_at: string | null;
};

export type ExecutionDetail = ExecutionSummary & {
  workflow_name?: string;
  context?: Record<string, unknown>;
  error_message?: string | null;
  step_history?: Array<{
    step_key: string;
    step_type: string;
    status: string;
    started_at: string;
    completed_at: string | null;
    output: Record<string, unknown>;
    next_step: string | null;
    error_message: string | null;
  }>;
};

export type AnalyticsPoint = {
  label: string;
  value: number;
};

export type TaskAnalyticsSummary = {
  tasks_executed: number;
  completed_tasks: number;
  failed_tasks: number;
  pending_tasks: number;
  running_tasks: number;
  agent_success_rate: number;
  average_execution_time_seconds: number;
  p95_execution_time_seconds: number;
  status_breakdown: AnalyticsPoint[];
  recent_task_volume: AnalyticsPoint[];
  execution_time_breakdown: AnalyticsPoint[];
};

export type RuntimeAnalyticsSummary = {
  runs_total: number;
  successful_runs: number;
  failed_runs: number;
  success_rate: number;
  average_execution_time_seconds: number;
  prompt_tokens_total: number;
  completion_tokens_total: number;
  total_tokens_total: number;
  average_tokens_per_run: number;
  provider_breakdown: AnalyticsPoint[];
  recent_token_usage: AnalyticsPoint[];
  execution_time_breakdown: AnalyticsPoint[];
};

import { getUser } from "@/lib/auth";

function getDefaultIds() {
  const user = typeof window !== "undefined" ? getUser() : null;
  return {
    tenantId: user?.tenant_id ?? "11111111-1111-1111-1111-111111111111",
    ownerId: user?.id ?? "22222222-2222-2222-2222-222222222222"
  };
}

export const platformServices: PlatformService[] = [
  {
    name: "auth-service",
    url: process.env.NEXT_PUBLIC_AUTH_SERVICE_URL ?? "http://localhost:8001",
    domain: "韬唤璁よ瘉涓庤闂帶鍒?
  },
  {
    name: "project-service",
    url: process.env.NEXT_PUBLIC_PROJECT_SERVICE_URL ?? "http://localhost:8002",
    domain: "椤圭洰绌洪棿涓庡崗浣滅鐞?
  },
  {
    name: "agent-service",
    url: process.env.NEXT_PUBLIC_AGENT_SERVICE_URL ?? "http://localhost:8003",
    domain: "鏅鸿兘鍛樺伐璧勪骇涓績"
  },
  {
    name: "task-service",
    url: process.env.NEXT_PUBLIC_TASK_SERVICE_URL ?? "http://localhost:8004",
    domain: "浠诲姟鐢熷懡鍛ㄦ湡绠＄悊"
  },
  {
    name: "workflow-service",
    url: process.env.NEXT_PUBLIC_WORKFLOW_SERVICE_URL ?? "http://localhost:8005",
    domain: "娴佺▼妯℃澘涓庨厤缃?
  },
  {
    name: "workflow-engine",
    url: process.env.NEXT_PUBLIC_WORKFLOW_ENGINE_URL ?? "http://localhost:8100",
    domain: "娴佺▼鎵ц寮曟搸"
  },
  {
    name: "agent-runtime",
    url: process.env.NEXT_PUBLIC_AGENT_RUNTIME_URL ?? "http://localhost:8200",
    domain: "Agent 杩愯鏃?
  }
];

function getTaskServiceUrl(path: string): string {
  const gateway = process.env.NEXT_PUBLIC_API_GATEWAY_URL;
  const taskUrl = process.env.NEXT_PUBLIC_TASK_SERVICE_URL ?? "http://localhost:8004";
  const base = gateway ?? taskUrl;
  const useGatewayPath = !!(gateway || /:8300(\/|$)/.test(base));
  const prefix = useGatewayPath ? "/api/tasks" : "/tasks";
  return `${base}${prefix}${path}`;
}

function getProjectServiceUrl(path: string): string {
  const gateway = process.env.NEXT_PUBLIC_API_GATEWAY_URL;
  const projectUrl = process.env.NEXT_PUBLIC_PROJECT_SERVICE_URL ?? "http://localhost:8002";
  const base = gateway ?? projectUrl;
  const useGatewayPath = !!(gateway || /:8300(\/|$)/.test(base));
  const prefix = useGatewayPath ? "/api/projects" : "/projects";
  return `${base}${prefix}${path}`;
}

function getAgentServiceUrl(path: string): string {
  const gateway = process.env.NEXT_PUBLIC_API_GATEWAY_URL;
  const agentUrl = process.env.NEXT_PUBLIC_AGENT_SERVICE_URL ?? "http://localhost:8003";
  const base = gateway ?? agentUrl;
  const prefix = gateway ? "/api/agents" : "/agents";
  return `${base}${prefix}${path}`;
}

/** AgentInstance / AgentTemplate API (agent-service /api/agent/* 鎴?/agent/*) */
function getAgentInstanceApiUrl(path: string): string {
  const gateway = process.env.NEXT_PUBLIC_API_GATEWAY_URL;
  const agentUrl = process.env.NEXT_PUBLIC_AGENT_SERVICE_URL ?? "http://localhost:8003";
  const base = gateway ?? agentUrl;
  const prefix = gateway ? "/api/agent" : "/agent";
  return `${base}${prefix}${path}`;
}

function getWorkflowServiceUrl(path: string): string {
  const gateway = process.env.NEXT_PUBLIC_API_GATEWAY_URL;
  const workflowUrl = process.env.NEXT_PUBLIC_WORKFLOW_SERVICE_URL ?? "http://localhost:8005";
  const base = gateway ?? workflowUrl;
  const useGatewayPath = !!(gateway || /:8300(\/|$)/.test(base));
  const prefix = useGatewayPath ? "/api/workflows" : "/workflows";
  return `${base}${prefix}${path}`;
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
  enabled?: boolean;
  default_tools?: string[];
  default_workflows?: string[];
  created_at?: string;
  description?: string | null;
  system_prompt?: string;
  config?: Record<string, unknown>;
};

/** 绉熸埛渚э細鑾峰彇 Agent 瀹炰緥璇︽儏 */
export async function getAgentInstance(
  instanceId: string
): Promise<AgentInstanceItem> {
  return safeRequest<AgentInstanceItem>(
    getAgentInstanceApiUrl(`/instances/${instanceId}`)
  );
}

/** 绉熸埛渚э細鏇存柊 Agent 瀹炰緥 */
export async function updateAgentInstance(
  instanceId: string,
  payload: {
    name?: string;
    description?: string | null;
    system_prompt?: string;
    model?: string;
    knowledge_base_id?: string | null;
    config?: Record<string, unknown>;
    enabled?: boolean;
  }
): Promise<AgentInstanceItem> {
  return safeRequest<AgentInstanceItem>(
    getAgentInstanceApiUrl(`/instances/${instanceId}`),
    { method: "PUT", body: JSON.stringify(payload) }
  );
}

export type AgentTemplateItem = {
  id: string;
  name: string;
  model: string;
  description?: string | null;
  default_tools?: string[];
  default_workflows?: string[];
  enabled?: boolean;
};

function getExecutionServiceUrl(path: string): string {
  const gateway = process.env.NEXT_PUBLIC_API_GATEWAY_URL;
  const engineUrl = process.env.NEXT_PUBLIC_WORKFLOW_ENGINE_URL ?? "http://localhost:8100";
  const base = gateway ?? engineUrl;
  const prefix = gateway ? "/api/executions" : "/api/v1/executions";
  return `${base}${prefix}${path}`;
}

async function safeRequest<T>(url: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...getAuthHeaders(),
    ...((init?.headers ?? {}) as Record<string, string>)
  };

  const response = await fetch(url, {
    ...init,
    headers,
    cache: "no-store"
  });

  if (response.status === 401) {
    if (typeof window !== "undefined") {
      clearToken();
      window.location.href = "/login";
    }
    throw new Error("Authentication required.");
  }

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function getServiceHealth(service: PlatformService): Promise<ServiceHealth | null> {
  try {
    return await safeRequest<ServiceHealth>(`${service.url}/health/live`);
  } catch {
    return null;
  }
}

export async function listProjects(): Promise<ProjectRecord[]> {
  const data = await safeRequest<{ items: ProjectRecord[] }>(getProjectServiceUrl(""));
  return data.items;
}

export type KnowledgeBaseItem = {
  id: string;
  name: string;
  slug?: string;
  description?: string | null;
  project_id: string;
};

export async function listProjectKnowledgeBases(projectId: string): Promise<KnowledgeBaseItem[]> {
  const data = await safeRequest<{ items?: KnowledgeBaseItem[] } | KnowledgeBaseItem[]>(
    getProjectServiceUrl(`/${projectId}/knowledge-bases`)
  );
  return Array.isArray(data) ? data : (data.items ?? []);
}

export async function createProject(payload: {
  name: string;
  description?: string;
  project_type?: "general" | "matrix_site";
  matrix_config?: Record<string, unknown>;
}): Promise<ProjectRecord> {
  return safeRequest<ProjectRecord>(getProjectServiceUrl(""), {
    method: "POST",
    body: JSON.stringify({
      tenant_id: getDefaultIds().tenantId,
      owner_id: getDefaultIds().ownerId,
      name: payload.name,
      description: payload.description ?? "",
      project_type: payload.project_type ?? "general",
      matrix_config: payload.matrix_config ?? {},
      team_members: []
    })
  });
}

export type SitePlanItem = {
  id: string;
  site_name: string;
  site_theme: string;
  target_audience: string;
  content_direction: string;
  seo_keywords: string[];
  site_structure: Record<string, unknown>;
  wordpress_site_id: string | null;
  status: "planned" | "building" | "active";
  created_at: string;
  updated_at: string;
};

export type SitePlan = {
  id: string;
  project_id: string;
  status: "draft" | "approved" | "executing";
  agent_input: Record<string, unknown>;
  agent_output: Record<string, unknown>;
  approved_at: string | null;
  approved_by: string | null;
  items: SitePlanItem[];
  created_at: string;
  updated_at: string;
};

export async function listSitePlans(
  projectId: string,
  params?: { status?: "draft" | "approved" | "executing"; limit?: number; offset?: number }
): Promise<{ items: SitePlan[]; total: number }> {
  const qs = new URLSearchParams();
  if (params?.status) qs.set("status", params.status);
  if (params?.limit) qs.set("limit", String(params.limit));
  if (params?.offset) qs.set("offset", String(params.offset));
  const suffix = qs.toString() ? `?${qs}` : "";
  return safeRequest<{ items: SitePlan[]; total: number }>(
    getProjectServiceUrl(`/${projectId}/site-plans${suffix}`)
  );
}

export async function createSitePlan(
  projectId: string,
  payload: {
    agent_input?: Record<string, unknown>;
    agent_output?: Record<string, unknown>;
    items?: Array<{
      site_name: string;
      site_theme: string;
      target_audience: string;
      content_direction: string;
      seo_keywords?: string[];
      site_structure?: Record<string, unknown>;
    }>;
  }
): Promise<SitePlan> {
  return safeRequest<SitePlan>(getProjectServiceUrl(`/${projectId}/site-plans`), {
    method: "POST",
    body: JSON.stringify({
      agent_input: payload.agent_input ?? {},
      agent_output: payload.agent_output ?? {},
      items: payload.items ?? [],
    }),
  });
}

export async function approveSitePlan(planId: string, approvedBy?: string): Promise<SitePlan> {
  return safeRequest<SitePlan>(getProjectServiceUrl(`/site-plans/${planId}/approve`), {
    method: "PATCH",
    body: JSON.stringify({
      approved_by: approvedBy ?? null,
    }),
  });
}

function getTaskRunsServiceUrl(path: string): string {
  const gateway = process.env.NEXT_PUBLIC_API_GATEWAY_URL;
  const workflowUrl = process.env.NEXT_PUBLIC_WORKFLOW_SERVICE_URL ?? "http://localhost:8005";
  const base = gateway ?? workflowUrl;
  const prefix = gateway ? "/api/task_runs" : "/task_runs";
  return `${base}${prefix}${path}`;
}

export type PlatformDomainItem = {
  id: string;
  domain: string;
  api_base_url: string;
  ssl_enabled: boolean;
};

export async function listPlatformDomainsAvailable(): Promise<PlatformDomainItem[]> {
  const data = await safeRequest<{ items: PlatformDomainItem[] }>(
    getProjectServiceUrl("/platform_domains/available")
  );
  return data.items ?? [];
}

export type QuotasResponse = {
  tenant_id: string;
  quotas: Record<string, { current: number; limit: number; allowed: boolean }>;
};

export async function getTenantQuotas(): Promise<QuotasResponse> {
  return safeRequest<QuotasResponse>(getProjectServiceUrl("/quotas"));
}

export async function createSiteBuildingBatch(payload: {
  project_id: string;
  count: number;
  domain_ids: string[];
  workflow_id?: string | null;
}): Promise<{ wordpress_site_ids: string[]; task_run_ids: string[] }> {
  return safeRequest<{ wordpress_site_ids: string[]; task_run_ids: string[] }>(
    getProjectServiceUrl("/site_building/batch"),
    {
      method: "POST",
      body: JSON.stringify({
        project_id: payload.project_id,
        count: payload.count,
        domain_ids: payload.domain_ids,
        workflow_id: payload.workflow_id ?? null
      })
    }
  );
}

export type TaskRunItem = {
  id: string;
  task_template_id: string | null;
  workflow_id: string;
  execution_id: string;
  status: string;
  start_time: string | null;
  end_time: string | null;
};

export type TaskRunDetail = TaskRunItem & {
  step_runs: Array<{
    id: string;
    step_name: string;
    status: string;
    duration: number;
    output_json: Record<string, unknown>;
  }>;
};

export type WordPressSiteRecord = {
  id: string;
  tenant_id: string;
  project_id: string;
  name: string;
  domain: string;
  api_url: string;
  username: string;
  status: string;
  created_at: string;
};

export async function listTaskRuns(params?: {
  project_id?: string;
  workflow_id?: string;
  status?: string;
  limit?: number;
  offset?: number;
}): Promise<{ items: TaskRunItem[]; total: number }> {
  const qs = new URLSearchParams();
  if (params?.project_id) qs.set("project_id", params.project_id);
  if (params?.workflow_id) qs.set("workflow_id", params.workflow_id);
  if (params?.status) qs.set("status", params.status);
  if (params?.limit) qs.set("limit", String(params.limit ?? 50));
  if (params?.offset) qs.set("offset", String(params.offset ?? 0));
  const path = qs.toString() ? `?${qs}` : "";
  return safeRequest<{ items: TaskRunItem[]; total: number }>(
    getTaskRunsServiceUrl(path)
  );
}

export async function getTaskRun(taskRunId: string): Promise<TaskRunDetail> {
  return safeRequest<TaskRunDetail>(getTaskRunsServiceUrl(`/${taskRunId}`));
}

export async function listWordPressSites(projectId?: string): Promise<WordPressSiteRecord[]> {
  const qs = projectId ? `?project_id=${projectId}` : "";
  return safeRequest<WordPressSiteRecord[]>(getProjectServiceUrl(`/sites${qs}`));
}

export async function listAgents(params?: { project_id?: string }): Promise<AgentRecord[]> {
  const qs = params?.project_id ? `?project_id=${params.project_id}` : "";
  const data = await safeRequest<{ items: AgentRecord[] }>(
    getAgentServiceUrl("") + qs
  );
  return data.items;
}

export async function createAgent(payload: {
  projectId: string;
  name: string;
  role: string;
  model: string;
  systemPrompt: string;
}): Promise<AgentRecord> {
  return safeRequest<AgentRecord>(getAgentServiceUrl(""), {
    method: "POST",
    body: JSON.stringify({
      project_id: payload.projectId,
      name: payload.name,
      role: payload.role,
      role_title: payload.role.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase()),
      model: payload.model,
      system_prompt: payload.systemPrompt,
      skills: [],
      tools: [],
      workflow_ids: []
    })
  });
}

/** 绉熸埛渚э細鍒楀嚭 Agent 瀹炰緥锛堜粠妯℃澘鍒涘缓锛夛紝鏀寔鎸?project_id 绛涢€?*/
export async function listAgentInstances(params?: {
  project_id?: string;
  template_id?: string;
  limit?: number;
  offset?: number;
}): Promise<{ items: AgentInstanceItem[]; total: number }> {
  const qs = new URLSearchParams();
  if (params?.project_id) qs.set("project_id", params.project_id);
  if (params?.template_id) qs.set("template_id", params.template_id);
  if (params?.limit) qs.set("limit", String(params.limit ?? 200));
  if (params?.offset) qs.set("offset", String(params.offset ?? 0));
  const path = qs.toString() ? `/instances?${qs}` : "/instances";
  return safeRequest<{ items: AgentInstanceItem[]; total: number }>(
    getAgentInstanceApiUrl(path)
  );
}

/** 绉熸埛渚э細鍒楀嚭鍙敤鐨?Agent 妯℃澘锛堢敤浜庛€屼粠妯℃澘鍒涘缓銆嶏級 */
export async function listAgentTemplates(params?: {
  enabled?: boolean;
  limit?: number;
}): Promise<{ items: AgentTemplateItem[]; total: number }> {
  const qs = new URLSearchParams();
  if (params?.enabled != null) qs.set("enabled", String(params.enabled));
  if (params?.limit) qs.set("limit", String(params.limit ?? 100));
  const path = qs.toString() ? `/templates?${qs}` : "/templates";
  return safeRequest<{ items: AgentTemplateItem[]; total: number }>(
    getAgentInstanceApiUrl(path)
  );
}

/** 绉熸埛渚э細浠庢ā鏉垮垱寤?Agent 瀹炰緥 */
export async function createAgentInstanceFromTemplate(payload: {
  template_id: string;
  project_id: string;
  name: string;
  description?: string | null;
}): Promise<AgentInstanceItem> {
  return safeRequest<AgentInstanceItem>(getAgentInstanceApiUrl("/instances"), {
    method: "POST",
    body: JSON.stringify({
      template_id: payload.template_id,
      project_id: payload.project_id,
      name: payload.name.trim(),
      description: payload.description?.trim() || null,
    }),
  });
}

export async function listTasks(params?: {
  project_id?: string;
  status?: string;
  limit?: number;
  offset?: number;
}): Promise<TaskRecord[]> {
  const searchParams = new URLSearchParams();
  if (params?.project_id) searchParams.set("project_id", params.project_id);
  if (params?.status) searchParams.set("status", params.status);
  if (params?.limit) searchParams.set("limit", String(params.limit));
  if (params?.offset) searchParams.set("offset", String(params.offset));
  const qs = searchParams.toString();
  const data = await safeRequest<{ items: TaskRecord[]; total?: number }>(
    getTaskServiceUrl("") + (qs ? `?${qs}` : "")
  );
  return data.items;
}

export async function createTask(payload: {
  projectId: string;
  title: string;
  description: string;
  agentId?: string;
  workflowId?: string;
}): Promise<TaskRecord> {
  return safeRequest<TaskRecord>(getTaskServiceUrl(""), {
    method: "POST",
    body: JSON.stringify({
      project_id: payload.projectId,
      title: payload.title,
      description: payload.description,
      agent_id: payload.agentId || null,
      workflow_id: payload.workflowId || null,
      input_payload: {}
    })
  });
}

export async function getTask(taskId: string): Promise<TaskDetailRecord> {
  return safeRequest<TaskDetailRecord>(getTaskServiceUrl(`/${taskId}`));
}

export async function runTask(taskId: string): Promise<{ task_id: string; status: string; queued?: boolean }> {
  return safeRequest<{ task_id: string; status: string; queued?: boolean }>(
    getTaskServiceUrl(`/${taskId}/run`),
    { method: "POST" }
  );
}

export async function cancelTask(taskId: string): Promise<{ task_id: string; status: string }> {
  return safeRequest<{ task_id: string; status: string }>(
    getTaskServiceUrl(`/${taskId}/cancel`),
    { method: "POST" }
  );
}

export async function listWorkflows(params?: { project_id?: string }): Promise<WorkflowRecord[]> {
  const qs = params?.project_id ? `?project_id=${params.project_id}` : "";
  const data = await safeRequest<{ items: WorkflowRecord[] }>(
    getWorkflowServiceUrl(qs)
  );
  return data.items;
}

export type WorkflowBuilderNode = {
  id: string;
  type: string;
  data: Record<string, unknown>;
  position?: { x: number; y: number };
};

export type WorkflowBuilderEdge = {
  id?: string;
  source: string;
  target: string;
  sourceHandle?: string | null;
  targetHandle?: string | null;
};

export type WorkflowBuilderDetail = {
  id: string;
  project_id: string;
  name: string;
  slug: string;
  version: number;
  status: string;
  nodes: WorkflowBuilderNode[];
  edges: WorkflowBuilderEdge[];
  configuration: { trigger_type: string; entry_node_id: string | null; metadata: Record<string, unknown> };
  created_at: string;
  updated_at: string;
};

export async function createWorkflowFromBuilder(payload: {
  project_id: string;
  name: string;
  slug?: string;
  status?: string;
  nodes: Array<{ id: string; type: string; data: Record<string, unknown>; position?: { x: number; y: number } }>;
  edges: Array<{ source: string; target: string; sourceHandle?: string | null; targetHandle?: string | null }>;
  configuration?: { trigger_type?: string; entry_node_id?: string | null; metadata?: Record<string, unknown> };
}): Promise<WorkflowBuilderDetail> {
  return safeRequest<WorkflowBuilderDetail>(
    getWorkflowServiceUrl("/builder"),
    {
      method: "POST",
      body: JSON.stringify({
        project_id: payload.project_id,
        name: payload.name,
        slug: payload.slug,
        status: payload.status ?? "draft",
        nodes: payload.nodes,
        edges: payload.edges,
        configuration: payload.configuration ?? { trigger_type: "manual", entry_node_id: null, metadata: {} }
      })
    }
  );
}

export async function getWorkflowBuilder(workflowId: string): Promise<WorkflowBuilderDetail> {
  return safeRequest<WorkflowBuilderDetail>(
    getWorkflowServiceUrl(`/${workflowId}/builder`)
  );
}

export async function updateWorkflowStatus(
  workflowId: string,
  status: "draft" | "active"
): Promise<WorkflowRecord> {
  return safeRequest<WorkflowRecord>(
    getWorkflowServiceUrl(`/${workflowId}`),
    {
      method: "PUT",
      body: JSON.stringify({ status })
    }
  );
}

export async function runWorkflow(payload: { workflow_id: string; input_payload?: Record<string, unknown> }): Promise<{ execution_id: string; workflow_id: string; status: string }> {
  return safeRequest<{ execution_id: string; workflow_id: string; status: string }>(
    getWorkflowServiceUrl(`/${payload.workflow_id}/execute`),
    {
      method: "POST",
      body: JSON.stringify({ workflow_id: payload.workflow_id, input_payload: payload.input_payload ?? {} })
    }
  );
}

export async function createWorkflow(payload: {
  projectId: string;
  name: string;
  steps: Array<{
    step_key: string;
    name: string;
    type: string;
    next_step: string | null;
    config: Record<string, unknown>;
  }>;
}): Promise<WorkflowRecord> {
  return safeRequest<WorkflowRecord>(getWorkflowServiceUrl(""), {
    method: "POST",
    body: JSON.stringify({
      project_id: payload.projectId,
      name: payload.name,
      status: "active",
      trigger_type: "manual",
      definition: {},
      steps: payload.steps.map((step) => ({
        step_key: step.step_key,
        name: step.name,
        type: step.type,
        config: step.config,
        next_step: step.next_step,
        retry_limit: 1,
        timeout_seconds: 180
      }))
    })
  });
}

export async function listExecutions(): Promise<ExecutionSummary[]> {
  const data = await safeRequest<{ items: ExecutionSummary[] }>(
    getExecutionServiceUrl("")
  );
  return data.items;
}

export async function getExecution(executionId: string): Promise<ExecutionDetail> {
  return safeRequest<ExecutionDetail>(getExecutionServiceUrl(`/${executionId}`));
}

export async function getTaskAnalytics(): Promise<TaskAnalyticsSummary> {
  return safeRequest<TaskAnalyticsSummary>(getTaskServiceUrl("/analytics"));
}

export async function getRuntimeAnalytics(): Promise<RuntimeAnalyticsSummary> {
  const gateway = process.env.NEXT_PUBLIC_API_GATEWAY_URL;
  const runtimeUrl = process.env.NEXT_PUBLIC_AGENT_RUNTIME_URL ?? "http://localhost:8200";
  const base = gateway ?? runtimeUrl;
  const path = "/api/v1/analytics/summary";
  return safeRequest<RuntimeAnalyticsSummary>(`${base}${path}`);
}

export type ToolRecord = {
  id: string;
  name: string;
  slug?: string;
  type?: string;
  description?: string;
};

/** List tools from tool-service. Returns empty when service is stub. */
export async function listTools(): Promise<ToolRecord[]> {
  try {
    const base = process.env.NEXT_PUBLIC_API_GATEWAY_URL ?? process.env.NEXT_PUBLIC_PROJECT_SERVICE_URL ?? "http://localhost:8300";
    const data = await safeRequest<{ items: ToolRecord[] }>(`${base}/api/tools`);
    return Array.isArray(data.items) ? data.items : [];
  } catch {
    return [];
  }
}

