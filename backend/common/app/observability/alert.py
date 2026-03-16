"""Alert webhook integration (Slack, PagerDuty, etc)."""
from __future__ import annotations

import json
import os

import httpx


def send_alert(
    title: str,
    message: str,
    severity: str = "warning",
    extra: dict | None = None,
) -> bool:
    """Send alert to configured webhook. Returns True if sent."""
    url = os.getenv("ALERT_WEBHOOK_URL")
    if not url:
        return False
    payload = {
        "title": title,
        "message": message,
        "severity": severity,
        **(extra or {}),
    }
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            return 200 <= resp.status_code < 300
    except Exception:
        return False
