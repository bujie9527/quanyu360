"""WordPress REST API client using Basic Auth (Application Password)."""
from __future__ import annotations

import base64
from dataclasses import dataclass

import httpx


@dataclass
class WordPressConnectionResult:
    success: bool
    message: str
    site_name: str | None = None
    wp_version: str | None = None


def test_wordpress_connection(api_url: str, username: str, app_password: str) -> WordPressConnectionResult:
    """
    Test WordPress REST API connection using Basic Auth (Application Password).
    Calls /wp/v2/users/me or /wp-json/wp/v2 (index) to verify credentials.
    """
    url = api_url.rstrip("/") + "/wp-json/wp/v2/users/me"
    auth_str = f"{username}:{app_password}"
    b64 = base64.b64encode(auth_str.encode()).decode()
    headers = {"Authorization": f"Basic {b64}"}

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url, headers=headers)
    except httpx.ConnectError as e:
        return WordPressConnectionResult(
            success=False,
            message=f"无法连接: {str(e)}",
        )
    except httpx.TimeoutException:
        return WordPressConnectionResult(success=False, message="连接超时")
    except Exception as e:
        return WordPressConnectionResult(success=False, message=f"请求失败: {str(e)}")

    if resp.status_code == 401:
        return WordPressConnectionResult(success=False, message="认证失败: 用户名或应用密码无效")

    if resp.status_code != 200:
        return WordPressConnectionResult(
            success=False,
            message=f"HTTP {resp.status_code}: {resp.text[:200] if resp.text else '未知错误'}",
        )

    try:
        data = resp.json()
        name = data.get("name") or data.get("slug") or username
        return WordPressConnectionResult(
            success=True,
            message="连接成功",
            site_name=name,
            wp_version=None,
        )
    except Exception:
        return WordPressConnectionResult(success=True, message="连接成功")
