"""AgentRuntime: 按 agent_id 加载 Agent，执行 run_task / run_workflow。集成 KnowledgeBase、ToolRegistry、Workflow。"""
from __future__ import annotations

import uuid
from typing import Any

import httpx

from app.core.agent_loader import AgentConfig
from app.core.agent_loader import AgentLoader
from app.core.config import get_settings
from app.core.llm import resolve_llm_adapter
from app.core.rag.context_builder import ContextBuilder
from app.core.rag.retriever import ProjectServiceRetriever
from app.core.runner import build_execution
from app.core.schemas import AgentExecutionResult
from app.core.schemas import AgentRunRequest
from app.core.schemas import RuntimeTaskPayload
from app.core.tooling import execute_registered_tool
from app.core.tooling import get_runtime_tool_registry


def _normalize_task_input(task_input: str | dict[str, Any]) -> RuntimeTaskPayload:
    """将 task_input 转为 RuntimeTaskPayload。"""
    if isinstance(task_input, str):
        return RuntimeTaskPayload(
            title=task_input.strip() or "Task",
            description=None,
            input_payload={},
        )
    if isinstance(task_input, dict):
        title = str(task_input.get("title", task_input.get("query", "")) or "Task").strip()
        desc = task_input.get("description") or task_input.get("content")
        payload = dict(task_input.get("input_payload") or task_input.get("input") or {})
        return RuntimeTaskPayload(title=title, description=desc, input_payload=payload)
    return RuntimeTaskPayload(title="Task", description=None, input_payload={})


class AgentRuntime:
    """
    按 agent_id 初始化的 Agent 运行时。
    初始化: 加载 Agent、Tools、KnowledgeBase、LLM
    Tools: 使用 tools_override，若为空则使用 AgentTemplate.default_tools；从 ToolRegistry 加载。
    执行: run_task(task_input) → RAG（如有知识库）→ LLM reasoning → 调用 Tools
    """

    def __init__(self, agent_id: str) -> None:
        self.agent_id = str(agent_id)
        self.settings = get_settings()
        self._config: AgentConfig | None = None
        self._llm_adapter = None
        self._retriever: ProjectServiceRetriever | None = None
        self._context_builder: ContextBuilder | None = None
        self._loader = AgentLoader()
        self._registry = None

    def _ensure_loaded(self) -> AgentConfig:
        """懒加载 Agent 配置、ToolRegistry、KnowledgeBase 检索组件。"""
        if self._config is not None:
            return self._config
        cfg = self._loader.load(self.agent_id)
        if cfg is None:
            raise RuntimeError(f"Agent not found: {self.agent_id}")
        self._config = cfg
        self._llm_adapter = resolve_llm_adapter(cfg.model)
        self._registry = get_runtime_tool_registry()
        if cfg.knowledge_base_id and cfg.project_id:
            self._retriever = ProjectServiceRetriever()
            self._context_builder = ContextBuilder()
        return self._config

    @property
    def effective_tools(self) -> list[str] | None:
        """Agent 可用工具列表：tools_override 或 AgentTemplate.default_tools。None 表示无限制。"""
        return self._ensure_loaded().allowed_tool_slugs

    def get_tool(self, tool_name: str):
        """从 ToolRegistry 加载工具。若 effective_tools 受限，则校验 tool_name 须在其中。"""
        cfg = self._ensure_loaded()
        slug = tool_name.strip().lower()
        if cfg.allowed_tool_slugs is not None:
            allowed = {s.strip().lower() for s in cfg.allowed_tool_slugs if isinstance(s, str)}
            if slug not in allowed:
                raise ValueError(f"Agent is not allowed to use tool '{tool_name}'.")
        return self._registry.get(tool_name)

    def execute_tool(
        self,
        tool_name: str,
        action: str,
        parameters: dict[str, Any],
        *,
        task_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """
        调用 ToolRegistry.get(tool_name) 获取工具，执行 tool.execute(action, parameters, context)。
        内部使用 execute_registered_tool（含限流、权限校验）。
        """
        cfg = self._ensure_loaded()
        meta = dict(metadata or {})
        meta.setdefault("project_id", cfg.project_id)
        if cfg.tenant_id:
            meta.setdefault("tenant_id", cfg.tenant_id)
        if cfg.allowed_tool_slugs is not None:
            meta["allowed_tool_slugs"] = cfg.allowed_tool_slugs
        return execute_registered_tool(
            tool_name=tool_name,
            action=action,
            parameters=parameters,
            agent_id=self.agent_id,
            task_id=task_id,
            project_id=cfg.project_id,
            metadata=meta,
        )

    @property
    def config(self) -> AgentConfig:
        """Agent 配置（加载后可用）。"""
        return self._ensure_loaded()

    def run_task(
        self,
        task_input: str | dict[str, Any],
        *,
        task_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AgentExecutionResult:
        """
        执行任务：task_input → RAG（如有知识库）→ LLM reasoning → 调用 Tools。

        task_input: str 或 dict。str 作为 title；dict 可含 title, description, input_payload/input。
        task_id: 可选，默认生成 UUID。
        metadata: 可选附加元数据（如 tenant_id）。
        """
        cfg = self._ensure_loaded()
        task_id = task_id or str(uuid.uuid4())
        task = _normalize_task_input(task_input)

        query_text = f"{task.title} {task.description or ''}".strip()
        if self._retriever and self._context_builder and cfg.knowledge_base_id and cfg.project_id and query_text:
            chunks = self._retriever.retrieve(
                query=query_text,
                knowledge_base_id=cfg.knowledge_base_id,
                project_id=cfg.project_id,
                limit=10,
            )
            if chunks:
                context_str = self._context_builder.build(chunks)
                if context_str:
                    rag_context = f"\n\n[知识库检索上下文]\n{context_str}\n"
                    task = RuntimeTaskPayload(
                        title=task.title,
                        description=(task.description or "") + rag_context,
                        input_payload=task.input_payload,
                        expected_output=task.expected_output,
                    )

        meta = dict(metadata or {})
        meta.setdefault("project_id", cfg.project_id)
        if cfg.tenant_id:
            meta.setdefault("tenant_id", cfg.tenant_id)
        if cfg.allowed_tool_slugs is not None:
            meta["allowed_tool_slugs"] = cfg.allowed_tool_slugs

        request = AgentRunRequest(
            agent_id=self.agent_id,
            task_id=task_id,
            model=cfg.model,
            system_prompt=cfg.system_prompt or "",
            task=task,
            metadata=meta,
        )
        return build_execution(request)

    def run_workflow(
        self,
        workflow_id: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        执行 Workflow。调用 WorkflowEngine（经 workflow-service）。
        Agent 作为执行者，agent_id 注入到 input_payload 供 workflow 节点使用。

        输入: workflow_id, params (即 input_payload)
        返回: { execution_id, workflow_id, status }
        """
        cfg = self._ensure_loaded()
        base_url = self.settings.workflow_service_url.rstrip("/")
        url = f"{base_url}/workflows/{workflow_id}/execute"
        input_payload = dict(params or {})
        input_payload.setdefault("agent_id", self.agent_id)
        if cfg.project_id:
            input_payload.setdefault("project_id", cfg.project_id)
        if cfg.tenant_id:
            input_payload.setdefault("tenant_id", cfg.tenant_id)
        payload = {"input_payload": input_payload}
        try:
            with httpx.Client(timeout=60.0) as client:
                resp = client.post(url, json=payload, headers={"Content-Type": "application/json"})
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as e:
            raise RuntimeError(
                f"Workflow execution failed: HTTP {e.response.status_code} - {e.response.text[:500]}"
            ) from e
        except httpx.RequestError as e:
            raise RuntimeError(f"Workflow service unreachable: {e!s}") from e

    def run_task_template(
        self,
        task_template_id: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        执行 TaskTemplate：获取 TaskTemplate → 获取 Workflow → 执行 Workflow。

        输入: task_template_id, params (作为 input_payload 传入 workflow)
        返回: { execution_id, workflow_id, status }
        """
        base_url = self.settings.workflow_service_url.rstrip("/")
        url = f"{base_url}/task_templates/{task_template_id}"
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.get(url)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as e:
            raise RuntimeError(
                f"TaskTemplate not found: HTTP {e.response.status_code} - {e.response.text[:500]}"
            ) from e
        except httpx.RequestError as e:
            raise RuntimeError(f"Workflow service unreachable: {e!s}") from e

        workflow_id = data.get("workflow_id") if data.get("workflow_id") else None
        if not workflow_id:
            raise RuntimeError(
                f"TaskTemplate '{task_template_id}' has no workflow_id. Cannot execute."
            )

        return self.run_workflow(str(workflow_id), params)
