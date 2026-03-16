"""Facebook/Meta Graph API connector. create_post, comment_post, send_message with rate limiting."""
from __future__ import annotations

import os
import time
from urllib.parse import urlencode
from typing import Any

import httpx

from tools.connectors.base import BaseConnector
from tools.connectors.base import ConnectorConfig

GRAPH_BASE = "https://graph.facebook.com/v25.0"
RATE_LIMIT_THRESHOLD = 0.75  # Pause when usage exceeds 75%
RATE_LIMIT_BACKOFF_BASE = 2.0  # seconds


def _resolve_config(config: ConnectorConfig) -> dict[str, Any]:
    """Merge connector_config with env. Credentials never logged."""
    token = config.get_str("access_token") or config.get_str("api_key")
    if not token:
        token = os.environ.get("FACEBOOK_ACCESS_TOKEN", "").strip()
    return {"access_token": token}


def _parse_app_usage(headers: httpx.Headers) -> dict[str, float]:
    """Parse X-App-Usage header: call_count, total_time, total_cputime (0-100%)."""
    raw = headers.get("x-app-usage")
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {}


def _check_rate_limit(headers: httpx.Headers) -> float:
    """
    Return seconds to sleep if approaching limit. 0 = no sleep.
    Facebook throttles around 75%; we sleep when any metric exceeds threshold.
    """
    usage = _parse_app_usage(headers)
    if not usage:
        return 0.0
    max_pct = max(
        usage.get("call_count", 0),
        usage.get("total_time", 0),
        usage.get("total_cputime", 0),
    )
    if max_pct >= RATE_LIMIT_THRESHOLD * 100:
        return max(5.0, (max_pct / 100) * 10)
    return 0.0


class FacebookConnector(BaseConnector):
    """Meta Graph API. Page posts, comments, Messenger. Includes rate limiting."""

    name = "facebook"

    def __init__(self) -> None:
        self._last_sleep_until = 0.0

    def execute(
        self,
        action: str,
        parameters: dict[str, Any],
        config: ConnectorConfig,
    ) -> dict[str, Any]:
        resolved = _resolve_config(config)
        token = resolved["access_token"]
        if not token:
            return {"success": False, "error": "Facebook access_token required (connector_config or FACEBOOK_ACCESS_TOKEN)"}

        timeout = config.get_int("timeout_seconds", 30)

        try:
            with httpx.Client(timeout=timeout) as client:
                if action == "create_post":
                    return self._create_post(client, token, parameters)
                if action == "comment_post":
                    return self._comment_post(client, token, parameters)
                if action == "send_message":
                    return self._send_message(client, token, parameters)
                return {"success": False, "error": f"Unknown action: {action}"}
        except httpx.TimeoutException as e:
            return {"success": False, "error": f"Request timeout: {e}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _maybe_sleep(self, headers: httpx.Headers) -> None:
        now = time.monotonic()
        if now < self._last_sleep_until:
            time.sleep(self._last_sleep_until - now)
        delay = _check_rate_limit(headers)
        if delay > 0:
            self._last_sleep_until = time.monotonic() + delay
            time.sleep(delay)

    def _request_with_retry(
        self,
        client: httpx.Client,
        method: str,
        url: str,
        *,
        json_body: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        max_retries: int = 3,
    ) -> tuple[httpx.Response, dict[str, Any]]:
        """Execute request, retry on 429 with exponential backoff, apply rate limiting."""
        last_error: dict[str, Any] = {}
        resp = client.request(method, url)  # init for fallback
        for attempt in range(max_retries):
            if json_body:
                resp = client.request(method, url, json=json_body)
            elif data:
                resp = client.request(method, url, data=data)
            else:
                resp = client.request(method, url)

            self._maybe_sleep(resp.headers)

            if resp.status_code == 429 or (resp.status_code >= 500 and attempt < max_retries - 1):
                try:
                    err = resp.json()
                except Exception:
                    err = {"error": {"message": resp.text}}
                last_error = err
                backoff = RATE_LIMIT_BACKOFF_BASE ** (attempt + 1)
                time.sleep(backoff)
                continue

            return resp, {}
        return resp, last_error if last_error else {"error": {"message": "Rate limited or server error"}}

    def _create_post(self, client: httpx.Client, token: str, params: dict[str, Any]) -> dict[str, Any]:
        page_id = params.get("page_id")
        message = params.get("message", "")
        link = params.get("link")

        if not page_id:
            return {"success": False, "error": "page_id required"}
        if not message and not link:
            return {"success": False, "error": "Either message or link must be supplied"}

        body: dict[str, Any] = {"access_token": token}
        if message:
            body["message"] = message
        if link:
            body["link"] = str(link)

        url = f"{GRAPH_BASE}/{page_id}/feed"
        resp, err = self._request_with_retry(client, "POST", url, data=body)
        return self._parse_response(resp, err)

    def _comment_post(self, client: httpx.Client, token: str, params: dict[str, Any]) -> dict[str, Any]:
        post_id = params.get("post_id")
        message = params.get("message", "")

        if not post_id:
            return {"success": False, "error": "post_id required"}
        if not message:
            return {"success": False, "error": "message required"}

        body = {"message": message, "access_token": token}
        url = f"{GRAPH_BASE}/{post_id}/comments"
        resp, err = self._request_with_retry(client, "POST", url, data=body)
        return self._parse_response(resp, err)

    def _send_message(self, client: httpx.Client, token: str, params: dict[str, Any]) -> dict[str, Any]:
        page_id = params.get("page_id")
        recipient_id = params.get("recipient_id")  # PSID
        message_text = params.get("message", "")
        messaging_type = params.get("messaging_type", "RESPONSE")

        if not page_id or not recipient_id:
            return {"success": False, "error": "page_id and recipient_id (PSID) required for send_message"}
        if not message_text:
            return {"success": False, "error": "message required"}

        body = {
            "recipient": {"id": str(recipient_id)},
            "messaging_type": str(messaging_type).upper(),
            "message": {"text": message_text},
        }
        url = f"{GRAPH_BASE}/{page_id}/messages?{urlencode({'access_token': token})}"
        resp, err = self._request_with_retry(client, "POST", url, json_body=body)
        return self._parse_response(resp, err)

    def _parse_response(self, resp: httpx.Response, fallback_err: dict[str, Any]) -> dict[str, Any]:
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
        if not success:
            err = data.get("error", {}) if isinstance(data, dict) else {}
            msg = err.get("message", fallback_err.get("error", {}).get("message", resp.text))
            out["error"] = msg
        return out
