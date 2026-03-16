from fastapi import APIRouter
from fastapi import HTTPException

from app.core.analytics import get_runtime_analytics_summary
from app.core.analytics import render_prometheus_metrics
from app.core.config import get_settings
from app.core.schemas import AgentRunRequest
from app.core.schemas import Plan
from app.core.schemas import PlanExecuteRequest
from app.core.schemas import PlanRequest
from app.core.schemas import TeamRunRequest
from app.core.schemas import RuntimeAnalyticsSummary
from app.core.schemas import RuntimeTaskPayload
from app.core.schemas import ToolCallRequestModel
from app.core.schemas import ToolSelectRequest
from app.core.agent_executor import AgentExecutor
from app.core.agent_runtime import AgentRuntime
from app.core.runner import build_execution
from app.core.plan_executor import PlanExecutor
from app.core.planner import Planner
from app.core.team_orchestrator import TeamOrchestrator
from app.core.tool_selector import ToolSelector
from app.core.tooling import execute_registered_tool
from app.core.tooling import list_registered_tools
from common.app.observability.health import build_health_status
from common.app.observability.prometheus import build_metrics_response

settings = get_settings()
router = APIRouter()


@router.get("/health/live", tags=["health"])
def live() -> dict:
    return build_health_status(settings.service_name, status="live").model_dump(mode="json")


@router.get("/health/ready", tags=["health"])
def ready() -> dict:
    return build_health_status(settings.service_name, status="ready").model_dump(mode="json")


@router.get("/metrics", tags=["observability"])
def metrics():
    summary = get_runtime_analytics_summary()
    return build_metrics_response(render_prometheus_metrics(summary))


@router.get(f"{settings.api_v1_prefix}/capabilities", tags=["runtime"])
def get_capabilities() -> dict:
    return {
        "service": settings.service_name,
        "default_model": settings.default_model,
        "tools": list_registered_tools(),
        "features": [
            "tool-execution",
            "tool-selection",
            "reflection",
            "agent-loop",
            "rag",
            "artifact-streaming",
            "policy-evaluation",
            "multi-agent-teams",
            "agent-planning",
        ],
    }


@router.get(f"{settings.api_v1_prefix}/tools", tags=["runtime"])
def get_tools() -> dict:
    return {
        "items": list_registered_tools(),
    }


@router.get(f"{settings.api_v1_prefix}/analytics/summary", response_model=RuntimeAnalyticsSummary, tags=["analytics"])
def get_runtime_analytics() -> RuntimeAnalyticsSummary:
    return get_runtime_analytics_summary()


@router.post(f"{settings.api_v1_prefix}/tools/select", tags=["runtime"])
def select_tool(payload: ToolSelectRequest) -> dict:
    """
    Task → LLM chooses tool.
    Returns selected tool_name, action, parameters.
    """
    selector = ToolSelector()
    call = selector.select(task=payload.task, model=payload.model)
    if not call:
        return {"selected": None, "message": "No tool selected for this task."}
    return {
        "selected": {
            "tool_name": call.tool_name,
            "action": call.action,
            "parameters": call.parameters,
            "rationale": call.rationale,
        },
    }


@router.post(f"{settings.api_v1_prefix}/tools/select-and-execute", tags=["runtime"])
def select_and_execute_tool(payload: ToolSelectRequest) -> dict:
    """
    Task → LLM chooses tool → Tool executed.
    """
    selector = ToolSelector()
    call = selector.select(task=payload.task, model=payload.model)
    if not call:
        return {"selected": None, "result": None, "message": "No tool selected for this task."}
    result = execute_registered_tool(
        tool_name=call.tool_name,
        action=call.action,
        parameters=call.parameters,
        agent_id=payload.agent_id,
        task_id=payload.task_id,
        metadata={"source": "tool-select-and-execute"},
    )
    return {
        "selected": {"tool_name": call.tool_name, "action": call.action, "parameters": call.parameters},
        "result": result.model_dump(mode="json"),
    }


@router.post(f"{settings.api_v1_prefix}/tools/execute", tags=["runtime"])
def execute_tool(payload: ToolCallRequestModel) -> dict:
    result = execute_registered_tool(
        tool_name=payload.tool_name,
        action=payload.action,
        parameters=payload.parameters,
        agent_id=payload.agent_id,
        task_id=payload.task_id,
        project_id=payload.project_id,
        metadata=payload.metadata,
    )
    return result.model_dump(mode="json")


@router.post(f"{settings.api_v1_prefix}/runs", tags=["runtime"])
def run_agent(payload: AgentRunRequest) -> dict:
    execution = build_execution(payload)
    return execution.model_dump(mode="json")


@router.post(f"{settings.api_v1_prefix}/runs/loop", tags=["runtime"])
def run_agent_loop(
    payload: AgentRunRequest,
    max_steps: int | None = None,
    timeout_seconds: int | None = None,
) -> dict:
    """
    Full agent execution loop: plan → select tool → execute → observe → reflect → update memory.
    Safety limits: max_steps, timeout_seconds.
    """
    executor = AgentExecutor()
    return executor.execute(
        payload,
        max_steps=max_steps,
        timeout_seconds=timeout_seconds,
    )


@router.post(f"{settings.api_v1_prefix}/teams/runs", tags=["runtime"])
def run_team(payload: TeamRunRequest) -> dict:
    orchestrator = TeamOrchestrator()
    result = orchestrator.run(payload)
    return result.model_dump(mode="json")


@router.post(f"{settings.api_v1_prefix}/agents/{{agent_id}}/run", tags=["runtime"])
def run_agent_by_id(agent_id: str, payload: dict) -> dict:
    """
    统一执行接口。支持格式：

    1. 新格式: { "type": "chat|workflow|task", "id": "...", "input": {} }
       - chat: LLM 对话，input 作为 task_input
       - workflow: 执行 WorkflowEngine，id=workflow_id
       - task: 执行 TaskTemplate，id=task_template_id

    2. 旧格式: task_input (str 或 dict)，等同于 type=chat
    """
    runtime = AgentRuntime(agent_id)
    run_type = (payload.get("type") or "").strip().lower()
    run_id = payload.get("id")
    run_input = payload.get("input") or {}

    if run_type == "workflow":
        if not run_id:
            raise HTTPException(status_code=400, detail="type=workflow requires id (workflow_id)")
        return runtime.run_workflow(str(run_id), run_input if isinstance(run_input, dict) else {})

    if run_type == "task":
        if not run_id:
            raise HTTPException(status_code=400, detail="type=task requires id (task_template_id)")
        return runtime.run_task_template(str(run_id), run_input if isinstance(run_input, dict) else {})

    # chat 或旧格式（无 type / task_input）
    task_input = payload.get("task_input", payload) if run_type in ("", "chat") else run_input
    result = runtime.run_task(task_input, metadata=payload.get("metadata"))
    return result.model_dump(mode="json")


@router.post(f"{settings.api_v1_prefix}/agents/{{agent_id}}/workflow/run", tags=["runtime"])
def run_agent_workflow(agent_id: str, payload: dict) -> dict:
    """
    执行 Workflow。Agent 作为执行者。
    Body: { "workflow_id": "...", "params": {} }
    """
    runtime = AgentRuntime(agent_id)
    workflow_id = payload.get("workflow_id")
    if not workflow_id:
        raise HTTPException(status_code=400, detail="Missing workflow_id")
    return runtime.run_workflow(str(workflow_id), payload.get("params"))


@router.post(f"{settings.api_v1_prefix}/agents/{{agent_id}}/task-template/run", tags=["runtime"])
def run_agent_task_template(agent_id: str, payload: dict) -> dict:
    """
    执行 TaskTemplate：获取 TaskTemplate → 获取 Workflow → 执行 Workflow。
    Body: { "task_template_id": "...", "params": {} }
    """
    runtime = AgentRuntime(agent_id)
    task_template_id = payload.get("task_template_id")
    if not task_template_id:
        raise HTTPException(status_code=400, detail="Missing task_template_id")
    return runtime.run_task_template(str(task_template_id), payload.get("params"))


# --- Agent Planning ---


@router.post(f"{settings.api_v1_prefix}/plan", response_model=Plan, tags=["planning"])
def create_plan(payload: PlanRequest) -> Plan:
    """Generate a plan (ordered steps) for a task using LLM."""
    planner = Planner()
    return planner.plan(payload.task, model=payload.model)


@router.post(f"{settings.api_v1_prefix}/rag/query", tags=["rag"])
def rag_query(payload: dict) -> dict:
    """
    RAG: query -> vector search -> retrieve -> add context -> generate.
    Body: query, knowledge_base_id, project_id, system_prompt?, retrieve_limit?, model?
    """
    from app.core.rag import RAGPipeline

    query = payload.get("query") or ""
    kb_id = payload.get("knowledge_base_id")
    project_id = payload.get("project_id")
    if not kb_id or not project_id:
        return {"content": "Missing knowledge_base_id or project_id.", "retrieved_count": 0, "context_used": False}
    pipeline = RAGPipeline()
    result = pipeline.run(
        query=query,
        knowledge_base_id=str(kb_id),
        project_id=str(project_id),
        system_prompt=payload.get("system_prompt"),
        retrieve_limit=payload.get("retrieve_limit", 10),
        model=payload.get("model", settings.default_model),
    )
    return {
        "content": result.content,
        "retrieved_count": result.retrieved_count,
        "context_used": result.context_used,
    }


@router.post(f"{settings.api_v1_prefix}/plan/execute", tags=["planning"])
def plan_and_execute(payload: PlanExecuteRequest) -> dict:
    """
    Task → Planner → Plan Steps → Executor.
    Generate plan and execute steps in order.
    """
    planner = Planner()
    plan = planner.plan(payload.task, model=payload.model)
    executor = PlanExecutor()
    results = executor.execute(
        plan,
        agent_id=payload.agent_id,
        task_id=payload.task_id,
        task_context={"task": payload.task.model_dump(mode="json")},
        stop_on_failure=payload.stop_on_failure,
    )
    return {
        "plan": plan.model_dump(mode="json"),
        "results": [r.to_dict() for r in results],
        "completed": len([r for r in results if r.success]),
        "failed": len([r for r in results if not r.success]),
    }
