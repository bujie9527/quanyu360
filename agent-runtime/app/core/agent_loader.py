"""Load Agent config from agent-service via HTTP."""
from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.core.config import get_settings


@dataclass
class AgentConfig:
    """Normalized agent config for runtime execution."""
    agent_id: str
    system_prompt: str
    model: str
    project_id: str
    tenant_id: str | None
    allowed_tool_slugs: list[str] | None  # None = unrestricted
    knowledge_base_id: str | None


class AgentLoader:
    """Fetch agent config from agent-service. Supports legacy Agent and AgentInstance."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._base_url = self.settings.agent_service_url.rstrip("/")

    def load(self, agent_id: str, *, agent_type: str | None = None) -> AgentConfig | None:
        """
        Load agent config. agent_type: 'agent' | 'instance' | None.
        If None, tries legacy Agent first, then AgentInstance.
        """
        if agent_type == "instance":
            return self._load_instance(agent_id)
        if agent_type == "agent":
            return self._load_legacy(agent_id)
        cfg = self._load_legacy(agent_id)
        if cfg is not None:
            return cfg
        return self._load_instance(agent_id)

    def _load_legacy(self, agent_id: str) -> AgentConfig | None:
        """Load legacy Agent: GET /agents/{id} + /agents/{id}/allowed-tools."""
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.get(f"{self._base_url}/agents/{agent_id}")
                if resp.status_code != 200:
                    return None
                data = resp.json()
                project_id = str(data.get("project_id", ""))
                if not project_id:
                    return None

                allowed_resp = client.get(f"{self._base_url}/agents/{agent_id}/allowed-tools")
                allowed_slugs: list[str] | None = None
                if allowed_resp.status_code == 200:
                    at_data = allowed_resp.json()
                    if not at_data.get("unrestricted", True):
                        allowed_slugs = list(at_data.get("allowed_tool_slugs") or [])

                return AgentConfig(
                    agent_id=agent_id,
                    system_prompt=str(data.get("system_prompt") or ""),
                    model=str(data.get("model") or self.settings.default_model),
                    project_id=project_id,
                    tenant_id=None,
                    allowed_tool_slugs=allowed_slugs,
                    knowledge_base_id=None,
                )
        except Exception:
            return None

    def _load_instance(self, agent_id: str) -> AgentConfig | None:
        """Load AgentInstance: GET /agent/instances/{id}."""
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.get(f"{self._base_url}/agent/instances/{agent_id}")
                if resp.status_code != 200:
                    return None
                data = resp.json()
                project_id = str(data.get("project_id", ""))
                if not project_id:
                    return None

                tools = data.get("tools_override") or data.get("default_tools") or []
                allowed_slugs = [str(t).strip().lower() for t in tools] if tools else None
                kb_id = data.get("knowledge_base_id")
                kb_str = str(kb_id) if kb_id else None

                return AgentConfig(
                    agent_id=agent_id,
                    system_prompt=str(data.get("system_prompt") or ""),
                    model=str(data.get("model") or self.settings.default_model),
                    project_id=project_id,
                    tenant_id=str(data["tenant_id"]) if data.get("tenant_id") else None,
                    allowed_tool_slugs=allowed_slugs,
                    knowledge_base_id=kb_str,
                )
        except Exception:
            return None
