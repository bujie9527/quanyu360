"""WordPress REST API connector. Supports publish, update, delete posts with secure credential handling."""
from __future__ import annotations

import os
from typing import Any

import httpx

from tools.connectors.base import BaseConnector
from tools.connectors.base import ConnectorConfig


def _resolve_config(config: ConnectorConfig) -> dict[str, Any]:
    """
    Merge connector_config with env fallback. Credentials never logged.
    Env: WORDPRESS_SITE_URL, WORDPRESS_USER, WORDPRESS_APP_PASSWORD
    """
    base_url = config.get_str("base_url") or config.get_str("site_url")
    if not base_url:
        base_url = os.environ.get("WORDPRESS_SITE_URL", "").strip()
    if base_url and not base_url.endswith("/wp-json"):
        base_url = base_url.rstrip("/") + "/wp-json"

    user = config.get_str("user") or config.get_str("username")
    if not user:
        user = os.environ.get("WORDPRESS_USER", "").strip()

    password = config.get_str("password") or config.get_str("app_password") or config.get_str("api_key")
    if not password:
        password = os.environ.get("WORDPRESS_APP_PASSWORD", "").strip()

    basic = config.get("basic_auth")
    if isinstance(basic, dict):
        user = basic.get("user") or user
        password = basic.get("password") or password

    return {"base_url": base_url, "user": user, "password": password}


class WordPressConnector(BaseConnector):
    """WordPress REST API v2. Uses Application Passwords (Basic Auth) or connector_config."""

    name = "wordpress"

    def execute(
        self,
        action: str,
        parameters: dict[str, Any],
        config: ConnectorConfig,
    ) -> dict[str, Any]:
        resolved = _resolve_config(config)
        base_url = resolved["base_url"]
        user = resolved["user"]
        password = resolved["password"]

        if not base_url:
            return {"success": False, "error": "WordPress site URL required (connector_config.base_url or WORDPRESS_SITE_URL)"}
        if not user or not password:
            return {"success": False, "error": "WordPress credentials required (basic_auth or WORDPRESS_USER, WORDPRESS_APP_PASSWORD)"}

        auth = httpx.BasicAuth(user, password)
        timeout = config.get_int("timeout_seconds", 30)

        try:
            with httpx.Client(auth=auth, timeout=timeout) as client:
                if action == "publish_post":
                    return self._create_post(client, base_url, parameters)
                if action == "update_post":
                    return self._update_post(client, base_url, parameters)
                if action == "delete_post":
                    return self._delete_post(client, base_url, parameters)
                return {"success": False, "error": f"Unknown action: {action}"}
        except httpx.TimeoutException as e:
            return {"success": False, "error": f"Request timeout: {e}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _create_post(self, client: httpx.Client, base_url: str, params: dict[str, Any]) -> dict[str, Any]:
        title = params.get("title") or ""
        content = params.get("content") or ""
        status = params.get("status", "draft")
        author = params.get("author")
        tags = params.get("tags") or []

        body: dict[str, Any] = {
            "title": title if isinstance(title, dict) else {"raw": str(title)},
            "content": content if isinstance(content, dict) else {"raw": str(content)},
            "status": str(status).lower() if status else "draft",
        }
        if author is not None:
            body["author"] = int(author) if isinstance(author, (int, str)) and str(author).isdigit() else author
        if tags:
            body["tags"] = [int(t) for t in tags if str(t).isdigit()] if isinstance(tags, list) else []

        url = base_url.rstrip("/") + "/wp/v2/posts"
        resp = client.post(url, json=body)
        return self._parse_response(resp, "create")

    def _update_post(self, client: httpx.Client, base_url: str, params: dict[str, Any]) -> dict[str, Any]:
        post_id = params.get("post_id")
        if not post_id:
            return {"success": False, "error": "post_id required for update_post"}

        body: dict[str, Any] = {}
        for key in ("title", "content", "status"):
            val = params.get(key)
            if val is not None:
                if key in ("title", "content") and isinstance(val, str):
                    body[key] = {"raw": val}
                else:
                    body[key] = val
        tags = params.get("tags")
        if tags is not None:
            body["tags"] = [int(t) for t in tags if str(t).isdigit()] if isinstance(tags, list) else []

        if not body:
            return {"success": False, "error": "At least one of title, content, status, tags must be provided"}

        url = f"{base_url.rstrip('/')}/wp/v2/posts/{int(post_id)}"
        resp = client.post(url, json=body)
        return self._parse_response(resp, "update")

    def _delete_post(self, client: httpx.Client, base_url: str, params: dict[str, Any]) -> dict[str, Any]:
        post_id = params.get("post_id")
        if not post_id:
            return {"success": False, "error": "post_id required for delete_post"}

        force = params.get("force", True)
        url = f"{base_url.rstrip('/')}/wp/v2/posts/{int(post_id)}"
        resp = client.delete(url, params={"force": "true" if force else "false"})
        return self._parse_response(resp, "delete")

    def _parse_response(self, resp: httpx.Response, action: str) -> dict[str, Any]:
        try:
            data = resp.json()
        except Exception:
            data = {"text": resp.text, "status_code": resp.status_code}

        success = 200 <= resp.status_code < 300
        out: dict[str, Any] = {
            "success": success,
            "status_code": resp.status_code,
            "data": data,
        }
        if not success and isinstance(data, dict):
            out["error"] = data.get("message", data.get("code", resp.text))
        return out
