"""Reflection system: Agent evaluates result after task execution."""
from __future__ import annotations

import json
import re
from typing import Any

import httpx
import structlog

from app.core.config import get_settings
from app.core.schemas import Reflection
from app.core.schemas import RuntimeTaskPayload


class ReflectionService:
    """
    After task execution, evaluates the result using LLM.
    Produces: success, issues, improvement for next run.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.logger = structlog.get_logger(self.settings.service_name).bind(component="reflection")

    def reflect(
        self,
        task: RuntimeTaskPayload,
        result: dict[str, Any],
        status: str,
        tool_results: list[dict[str, Any]] | None = None,
        model: str | None = None,
    ) -> Reflection:
        """
        Evaluate execution result and produce reflection.
        Falls back to heuristic when LLM unavailable.
        """
        model = model or self.settings.default_model
        raw = self._call_llm(task, result, status, tool_results or [], model)
        if raw:
            return self._parse_reflection(raw)
        return self._fallback_reflection(status, result)

    def _call_llm(
        self,
        task: RuntimeTaskPayload,
        result: dict[str, Any],
        status: str,
        tool_results: list[dict[str, Any]],
        model: str,
    ) -> dict[str, Any] | None:
        """Call LLM for reflection. Returns parsed JSON or None."""
        api_key = self.settings.openai_api_key or self.settings.claude_api_key
        if not api_key:
            return None

        base_url = self.settings.openai_base_url
        task_text = f"{task.title}\n{task.description or ''}".strip()
        result_str = json.dumps(result, ensure_ascii=False, indent=0)[:2000]
        tools_str = json.dumps(tool_results[:5], ensure_ascii=False)[:1000] if tool_results else "[]"

        system = (
            "You are an agent self-evaluation system. Given a task and its execution result, output a JSON object with: "
            "success (boolean), issues (array of short strings), improvement (string). "
            "Example: {\"success\":true,\"issues\":[\"article too short\"],\"improvement\":\"add more sections\"}. "
            "Respond with ONLY valid JSON, no markdown."
        )
        user = f"Task: {task_text}\n\nStatus: {status}\n\nResult: {result_str}\n\nTool results: {tools_str}\n\nOutput JSON:"

        payload: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
            "max_tokens": 512,
        }

        url = f"{base_url.rstrip('/')}/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        try:
            with httpx.Client(timeout=float(self.settings.llm_request_timeout_seconds)) as client:
                resp = client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
        except (httpx.HTTPError, json.JSONDecodeError) as exc:
            self.logger.warning("LLM reflection failed.", error=str(exc))
            return None

        choices = data.get("choices", [])
        if not choices:
            return None
        content = choices[0].get("message", {}).get("content", "").strip()
        if not content:
            return None

        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```\s*$", "", content)
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return None

    def _parse_reflection(self, raw: dict[str, Any]) -> Reflection:
        success = bool(raw.get("success", True))
        issues = raw.get("issues", [])
        if not isinstance(issues, list):
            issues = [str(issues)] if issues else []
        issues = [str(i) for i in issues[:20]]
        improvement = str(raw.get("improvement", "") or "")[:500]
        return Reflection(success=success, issues=issues, improvement=improvement)

    def _fallback_reflection(self, status: str, result: dict[str, Any]) -> Reflection:
        success = status == "completed"
        issues: list[str] = []
        improvement = ""
        if not success:
            err = result.get("content") or result.get("raw", {}).get("error", "")
            issues = [err[:200]] if err else ["Execution failed"]
            improvement = "Review error and retry with corrected inputs."
        return Reflection(success=success, issues=issues, improvement=improvement)
