"""Agent Planning module: Task → Planner → Plan Steps → Executor."""
from __future__ import annotations

import json
import re
from typing import Any

import httpx
import structlog

from app.core.config import get_settings
from app.core.schemas import Plan
from app.core.schemas import PlanStep
from app.core.schemas import RuntimeTaskPayload


def validate_plan_steps(steps: list[PlanStep]) -> list[PlanStep]:
    """
    Validate plan steps: ensure non-empty, reasonable length, no duplicates by content.
    """
    seen: set[str] = set()
    validated: list[PlanStep] = []
    for s in steps:
        normalized = s.step.strip().lower()
        if not normalized or len(s.step) > 500:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        validated.append(PlanStep(step=s.step.strip()))
    if not validated:
        raise ValueError("Plan validation failed: no valid steps produced.")
    return validated


class Planner:
    """
    Uses LLM to break a task into smaller, ordered steps.
    Output: structured Plan with list[PlanStep].
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.logger = structlog.get_logger(self.settings.service_name).bind(component="planner")

    def plan(self, task: RuntimeTaskPayload, model: str | None = None) -> Plan:
        """
        Generate a plan (ordered steps) for the given task using LLM.
        Falls back to heuristic plan when LLM is unavailable.
        """
        model = model or self.settings.default_model
        raw_plan = self._call_llm(task, model)
        if raw_plan:
            return self._parse_and_validate(raw_plan)
        return self._fallback_plan(task)

    def _call_llm(self, task: RuntimeTaskPayload, model: str) -> list[dict[str, Any]] | None:
        """Call LLM for structured plan. Returns parsed steps or None on failure.
        Uses OpenAI-compatible /chat/completions API (works with OpenAI, OpenRouter, etc.).
        """
        api_key = self.settings.openai_api_key or self.settings.claude_api_key
        if not api_key:
            self.logger.debug("No LLM API key configured, using fallback plan.")
            return None

        base_url = self.settings.openai_base_url

        task_text = f"{task.title}\n{task.description or ''}".strip()
        system = (
            "You are a task planner. Given a task, output a JSON array of steps ONLY. "
            "Each step is an object with a single key 'step' (short action description). "
            "Example: [{\"step\":\"research keywords\"},{\"step\":\"generate article\"},{\"step\":\"publish wordpress\"},{\"step\":\"share facebook\"}]. "
            "Respond with ONLY valid JSON, no markdown or extra text."
        )
        user = f"Task: {task_text}\n\nOutput JSON array of steps:"

        payload: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
            "max_tokens": 1024,
        }

        url = f"{base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=float(self.settings.llm_request_timeout_seconds)) as client:
                resp = client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
        except (httpx.HTTPError, json.JSONDecodeError) as exc:
            self.logger.warning("LLM plan request failed, using fallback.", error=str(exc))
            return None

        choices = data.get("choices", [])
        if not choices:
            return None
        content = choices[0].get("message", {}).get("content", "")
        if not content:
            return None

        return self._extract_steps_from_content(content)

    def _extract_steps_from_content(self, content: str) -> list[dict[str, Any]] | None:
        """Extract steps array from LLM response (handles markdown code blocks)."""
        content = content.strip()
        # Strip markdown code block if present
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```\s*$", "", content)
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            return None
        if isinstance(parsed, list):
            return [{"step": str(item.get("step", item) if isinstance(item, dict) else item)} for item in parsed]
        if isinstance(parsed, dict) and "steps" in parsed:
            return [
                {"step": str(s.get("step", s) if isinstance(s, dict) else s)}
                for s in parsed["steps"]
            ]
        return None

    def _parse_and_validate(self, raw_steps: list[dict[str, Any]]) -> Plan:
        """Parse raw steps into Plan and validate."""
        steps = [PlanStep(step=s["step"]) for s in raw_steps if isinstance(s.get("step"), str)]
        validated = validate_plan_steps(steps)
        return Plan(steps=validated)

    def _fallback_plan(self, task: RuntimeTaskPayload) -> Plan:
        """Heuristic plan when LLM is unavailable."""
        task_lower = (f"{task.title} {task.description or ''}".strip()).lower()
        steps: list[PlanStep] = []

        if any(k in task_lower for k in ["article", "blog", "post", "content", "wordpress"]):
            steps.extend([
                PlanStep(step="research keywords"),
                PlanStep(step="generate article"),
                PlanStep(step="publish wordpress"),
                PlanStep(step="share facebook"),
            ])
        elif any(k in task_lower for k in ["social", "share", "facebook"]):
            steps.extend([
                PlanStep(step="prepare content"),
                PlanStep(step="share facebook"),
            ])
        else:
            steps.extend([
                PlanStep(step="analyze requirements"),
                PlanStep(step="execute task"),
                PlanStep(step="report results"),
            ])

        return Plan(steps=steps)
