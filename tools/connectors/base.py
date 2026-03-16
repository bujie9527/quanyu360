"""Connector base for tool integrations with credential/config support."""
from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Any


class ConnectorConfig:
    """Per-invocation config (e.g. from platform Tool.config)."""

    def __init__(self, raw: dict[str, Any] | None = None) -> None:
        self._raw = raw or {}

    def get(self, key: str, default: Any = None) -> Any:
        return self._raw.get(key, default)

    def get_str(self, key: str, default: str = "") -> str:
        v = self._raw.get(key)
        return str(v) if v is not None else default

    def get_int(self, key: str, default: int = 0) -> int:
        v = self._raw.get(key)
        if v is None:
            return default
        try:
            return int(v)
        except (TypeError, ValueError):
            return default

    def get_auth_header(self) -> dict[str, str]:
        """Build Authorization header from common config keys."""
        api_key = self.get_str("api_key") or self.get_str("API_KEY")
        if api_key:
            return {"Authorization": f"Bearer {api_key}"}
        basic = self.get("basic_auth")
        if isinstance(basic, dict) and basic.get("user") and basic.get("password"):
            import base64

            cred = base64.b64encode(
                f"{basic['user']}:{basic['password']}".encode()
            ).decode()
            return {"Authorization": f"Basic {cred}"}
        return {}

    @property
    def base_url(self) -> str:
        return self.get_str("base_url") or self.get_str("endpoint", "").rstrip("/")


class BaseConnector(ABC):
    """Base for connectors that integrate with external APIs."""

    name: str = ""

    @abstractmethod
    def execute(
        self,
        action: str,
        parameters: dict[str, Any],
        config: ConnectorConfig,
    ) -> dict[str, Any]:
        """Execute an action with given parameters and connector config."""
        raise NotImplementedError
