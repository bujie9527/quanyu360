"""HTTP/REST API connector for external integrations."""
from __future__ import annotations

import json
from typing import Any

import httpx

from tools.connectors.base import BaseConnector
from tools.connectors.base import ConnectorConfig


class HttpConnector(BaseConnector):
    """Generic REST API connector. Uses Tool.config for base_url, api_key, headers."""

    name = "http"

    def execute(
        self,
        action: str,
        parameters: dict[str, Any],
        config: ConnectorConfig,
    ) -> dict[str, Any]:
        base_url = config.base_url
        if not base_url:
            return {"success": False, "error": "base_url or endpoint required in config"}

        # action format: METHOD /path or just /path (default GET)
        parts = action.strip().split(maxsplit=1)
        method = parts[0].upper() if len(parts) > 1 and parts[0] in ("GET", "POST", "PUT", "PATCH", "DELETE") else "GET"
        path = parts[1] if len(parts) > 1 else parts[0]
        if not path.startswith("/"):
            path = "/" + path

        url = base_url.rstrip("/") + path
        headers = dict(config.get("headers") or {})
        headers.update(config.get_auth_header())
        headers.setdefault("Content-Type", "application/json")

        timeout = config.get_int("timeout_seconds", 30)
        params = parameters.get("query") or {}
        body = parameters.get("body")
        if body is None and method in ("POST", "PUT", "PATCH"):
            body = parameters

        try:
            with httpx.Client(timeout=timeout) as client:
                if method == "GET":
                    resp = client.get(url, params=params, headers=headers)
                elif method == "POST":
                    resp = client.post(url, params=params, content=json.dumps(body) if body else None, headers=headers)
                elif method == "PUT":
                    resp = client.put(url, params=params, content=json.dumps(body) if body else None, headers=headers)
                elif method == "PATCH":
                    resp = client.patch(url, params=params, content=json.dumps(body) if body else None, headers=headers)
                elif method == "DELETE":
                    resp = client.delete(url, params=params, headers=headers)
                else:
                    return {"success": False, "error": f"Unsupported method {method}"}

                try:
                    data = resp.json()
                except Exception:
                    data = {"text": resp.text, "status_code": resp.status_code}

                return {
                    "success": 200 <= resp.status_code < 300,
                    "status_code": resp.status_code,
                    "data": data,
                }
        except httpx.TimeoutException as e:
            return {"success": False, "error": f"Request timeout: {e}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
