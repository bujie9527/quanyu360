"""Tool selection: Task → LLM chooses tool → Tool executed."""
from __future__ import annotations

import json
import re
from typing import Any

import httpx
import structlog

from app.core.config import get_settings
from app.core.schemas import PlannedToolCall
from app.core.schemas import RuntimeTaskPayload
from app.core.tooling import list_registered_tools


class ToolSelector:
    """
    Uses LLM to select a tool for a task.
    Consumes tool metadata (name, description, parameters) and outputs selected tool in JSON.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.logger = structlog.get_logger(self.settings.service_name).bind(component="tool-selector")

    def select(
        self,
        task: RuntimeTaskPayload,
        available_tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
    ) -> PlannedToolCall | None:
        """
        Select a tool for the task using LLM.
        Returns PlannedToolCall or None if no tool selected / LLM unavailable.
        """
        tools = available_tools if available_tools is not None else list_registered_tools()
        if not tools:
            self.logger.warning("No tools available for selection.")
            return None

        model = model or self.settings.default_model
        raw = self._call_llm(task, tools, model)
        if not raw:
            return self._fallback_select(task, tools)

        return self._parse_and_validate(raw, tools)

    def _build_tools_schema(self, tools: list[dict[str, Any]]) -> str:
        """Format tool metadata for LLM prompt."""
        entries = []
        for t in tools:
            name = t.get("name", "")
            desc = t.get("description", "")
            actions = t.get("actions", [])
            action_strs = []
            for a in actions:
                params = a.get("parameters", [])
                param_list = ", ".join(f"{p.get('name')}: {p.get('type', 'string')}" for p in params)
                action_strs.append(f"  - {a.get('name', '')}({param_list}): {a.get('description', '')}")
            entries.append(f"- {name}: {desc}\n" + "\n".join(action_strs))
        return "\n\n".join(entries)

    def _call_llm(
        self,
        task: RuntimeTaskPayload,
        tools: list[dict[str, Any]],
        model: str,
    ) -> dict[str, Any] | None:
        """Call LLM for tool selection. Returns parsed JSON or None."""
        api_key = self.settings.openai_api_key or self.settings.claude_api_key
        if not api_key:
            self.logger.debug("No LLM API key, using fallback selection.")
            return None

        base_url = self.settings.openai_base_url
        tools_schema = self._build_tools_schema(tools)
        task_text = f"{task.title}\n{task.description or ''}\n{json.dumps(task.input_payload or {}, ensure_ascii=False)}".strip()

        system = (
            "You are a tool selector. Given a user task and available tools, output exactly one tool call in JSON. "
            "Output ONLY valid JSON with keys: tool_name, action, parameters (object). "
            "Example: {\"tool_name\":\"wordpress\",\"action\":\"publish_post\",\"parameters\":{\"title\":\"My Post\",\"content\":\"Body\",\"status\":\"draft\"}}. "
            "Select the most relevant tool and action. Infer parameters from the task. Respond with ONLY the JSON object, no markdown."
        )
        user = f"Task:\n{task_text}\n\nAvailable tools:\n{tools_schema}\n\nOutput JSON:"

        payload: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.1,
            "max_tokens": 1024,
        }

        url = f"{base_url.rstrip('/')}/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        try:
            with httpx.Client(timeout=float(self.settings.llm_request_timeout_seconds)) as client:
                resp = client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
        except (httpx.HTTPError, json.JSONDecodeError) as exc:
            self.logger.warning("LLM tool selection failed.", error=str(exc))
            return None

        choices = data.get("choices", [])
        if not choices:
            return None
        content = choices[0].get("message", {}).get("content", "").strip()
        if not content:
            return None

        return self._extract_json(content)

    def _extract_json(self, content: str) -> dict[str, Any] | None:
        """Extract JSON object from LLM response."""
        content = content.strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```\s*$", "", content)
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return None

    def _parse_and_validate(
        self,
        raw: dict[str, Any],
        tools: list[dict[str, Any]],
    ) -> PlannedToolCall | None:
        """Parse and validate LLM output against available tools."""
        tool_name = raw.get("tool_name")
        action = raw.get("action")
        parameters = raw.get("parameters")
        if not isinstance(tool_name, str) or not isinstance(action, str):
            return None
        if parameters is None:
            parameters = {}
        if not isinstance(parameters, dict):
            parameters = {}

        tools_by_name = {t["name"]: t for t in tools}
        if tool_name not in tools_by_name:
            self.logger.warning("LLM selected unknown tool.", tool_name=tool_name)
            return None

        tool_def = tools_by_name[tool_name]
        actions = {a["name"]: a for a in tool_def.get("actions", [])}
        if action not in actions:
            self.logger.warning("LLM selected unknown action.", tool_name=tool_name, action=action)
            return None

        return PlannedToolCall(
            tool_name=tool_name,
            action=action,
            parameters=parameters,
            metadata={"source": "tool-selector"},
            rationale=f"Selected by LLM for task.",
        )

    def _fallback_select(
        self,
        task: RuntimeTaskPayload,
        tools: list[dict[str, Any]],
    ) -> PlannedToolCall | None:
        """Heuristic fallback when LLM unavailable."""
        task_lower = (f"{task.title} {task.description or ''} {task.input_payload or {}}").lower()
        tools_by_name = {t["name"]: t for t in tools}

        if "wordpress" in tools_by_name and any(k in task_lower for k in ["wordpress", "blog", "article", "publish", "post"]):
            payload = task.input_payload or {}
            return PlannedToolCall(
                tool_name="wordpress",
                action="publish_post",
                parameters={
                    "title": payload.get("title", task.title),
                    "content": payload.get("content", task.description or task.title),
                    "status": payload.get("status", "draft"),
                    "author": payload.get("author"),
                    "tags": payload.get("tags", []),
                },
                metadata={"source": "tool-selector-fallback"},
                rationale="Heuristic: task mentions publishing content.",
            )
        if "facebook" in tools_by_name and any(k in task_lower for k in ["facebook", "social", "share"]):
            payload = task.input_payload or {}
            return PlannedToolCall(
                tool_name="facebook",
                action="create_post",
                parameters={
                    "page_id": payload.get("page_id", "demo_page"),
                    "message": payload.get("message", task.description or task.title),
                    "link": payload.get("link"),
                },
                metadata={"source": "tool-selector-fallback"},
                rationale="Heuristic: task mentions social sharing.",
            )

        return None
