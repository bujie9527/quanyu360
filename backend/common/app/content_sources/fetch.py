"""Content Source 拉取实现：fetch_from_api, fetch_from_rss。"""
from __future__ import annotations

from typing import Any
from typing import Protocol

import httpx

from common.app.content_sources.schema_utils import apply_schema
from common.app.content_sources.types import ContentItem


class ContentSourceLike(Protocol):
    """ContentSource 模型或兼容对象的协议。"""
    type: str
    api_endpoint: str
    auth: dict[str, Any]
    schema: dict[str, Any]


def _build_headers(auth: dict[str, Any] | None) -> dict[str, str]:
    """根据 auth 配置构建请求头。"""
    auth = auth or {}
    headers = {"Accept": "application/json", "User-Agent": "AiWorkerCenter-ContentSource/1.0"}
    if auth.get("type") == "bearer" and auth.get("token"):
        headers["Authorization"] = f"Bearer {auth['token']}"
    if auth.get("type") == "api_key":
        key = auth.get("api_key")
        header_name = auth.get("header_name", "X-API-Key")
        if key:
            headers[header_name] = str(key)
    for k, v in auth.get("headers", {}).items():
        if isinstance(v, str):
            headers[k] = v
    return headers


def fetch_from_api(
    api_endpoint: str,
    auth: dict[str, Any] | None = None,
    schema: dict[str, Any] | None = None,
    *,
    method: str = "GET",
    timeout: float = 30.0,
) -> list[dict[str, Any]]:
    """
    从 API 拉取内容并返回统一结构列表。
    预期 API 返回 JSON，且包含数组（通过 schema.items_path 指定，默认 "items" 或 "data"）。
    """
    headers = _build_headers(auth)
    url = api_endpoint.strip()

    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.request(method, url, headers=headers)
    except httpx.ConnectError as e:
        raise RuntimeError(f"连接失败: {e}") from e
    except httpx.TimeoutException:
        raise RuntimeError("请求超时")

    if resp.status_code >= 400:
        raise RuntimeError(f"API 错误: HTTP {resp.status_code}")

    try:
        data = resp.json()
    except Exception as e:
        raise RuntimeError(f"解析 JSON 失败: {e}") from e

    # 定位数组
    items_path = (schema or {}).get("items_path")
    if items_path:
        parts = items_path.replace("]", "").replace("[", ".").split(".")
        cur = data
        for p in parts:
            if p and isinstance(cur, (dict, list)):
                cur = cur.get(p) if isinstance(cur, dict) else (cur[int(p)] if p.isdigit() else None)
        items = cur if isinstance(cur, list) else []
    else:
        items = data.get("items") or data.get("data") or data.get("results")
        if not isinstance(items, list):
            items = [data] if data is not None else []

    result = []
    for item in items:
        unified = apply_schema(item, schema)
        result.append(unified)
    return result


def fetch_from_rss(
    api_endpoint: str,
    auth: dict[str, Any] | None = None,
    schema: dict[str, Any] | None = None,
    *,
    timeout: float = 30.0,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    从 RSS/Atom 源拉取内容并返回统一结构列表。
    RSS 默认映射: title, content(description/summary), tags(category)。
    """
    try:
        import xml.etree.ElementTree as ET
    except ImportError:
        raise RuntimeError("需要 Python xml 支持")

    headers = _build_headers(auth)
    headers["Accept"] = "application/rss+xml, application/xml, text/xml, */*"
    url = api_endpoint.strip()

    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(url, headers=headers)
    except httpx.ConnectError as e:
        raise RuntimeError(f"连接失败: {e}") from e
    except httpx.TimeoutException:
        raise RuntimeError("请求超时")

    if resp.status_code >= 400:
        raise RuntimeError(f"RSS 拉取失败: HTTP {resp.status_code}")

    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as e:
        raise RuntimeError(f"解析 XML 失败: {e}") from e

    # RSS 2.0: channel/item; Atom: feed/entry
    ns = {"atom": "http://www.w3.org/2005/Atom", "dc": "http://purl.org/dc/elements/1.1/"}
    items = root.findall(".//item") or root.findall(".//atom:entry", ns)
    if not items:
        items = root.findall(".//{http://www.w3.org/2005/Atom}entry")

    schema = schema or {}
    title_tag = schema.get("title", "title")
    content_tag = schema.get("content", "description")  # description or content
    tags_tag = schema.get("tags", "category")

    def _find_elem(elem, tag: str):
        e = elem.find(tag)
        if e is not None:
            return e
        for uri in ("http://www.w3.org/2005/Atom", "http://purl.org/dc/elements/1.1/"):
            e = elem.find(f"{{{uri}}}{tag}")
            if e is not None:
                return e
        return None

    def _elem_text(elem, tag: str) -> str:
        e = _find_elem(elem, tag)
        return (e.text or "").strip() if e is not None else ""

    def _elem_content(elem, tag: str) -> str:
        e = _find_elem(elem, tag)
        if e is None:
            return ""
        t = (e.text or "").strip()
        if t:
            return t
        return ET.tostring(e, encoding="unicode", method="html")[:5000] if e else ""

    def _elem_tags(elem, tag: str) -> list[str]:
        tags = []
        for e in elem.findall(tag):
            t = (e.text or "").strip() or e.get("term", "")
            if t:
                tags.append(t)
        for uri in ("http://www.w3.org/2005/Atom", "http://purl.org/dc/elements/1.1/"):
            for e in elem.findall(f"{{{uri}}}{tag}"):
                t = (e.text or "").strip() or e.get("term", "")
                if t:
                    tags.append(t)
        return tags

    result = []
    for item in items[:limit]:
        title = _elem_text(item, title_tag) or _elem_text(item, "title")
        content = _elem_content(item, content_tag) or _elem_text(item, "description")
        if not content:
            content = _elem_content(item, "content") or _elem_content(item, "summary")
        tags = _elem_tags(item, tags_tag) or _elem_tags(item, "category")
        result.append({"title": title, "content": content, "tags": tags})
    return result


def fetch(
    source: ContentSourceLike | dict[str, Any],
    *,
    timeout: float = 30.0,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    根据 source.type 自动调度到 fetch_from_api 或 fetch_from_rss。
    返回统一结构列表：[{"title": "...", "content": "...", "tags": []}, ...]
    source 可为 ContentSource 模型或 dict。
    """
    if isinstance(source, dict):
        enabled = source.get("enabled", True)
        t = source.get("type", "api")
        api_endpoint = source.get("api_endpoint", "")
        auth = source.get("auth") or {}
        schema = source.get("schema") or {}
    else:
        enabled = getattr(source, "enabled", True)
        t = getattr(source.type, "value", source.type) if hasattr(source.type, "value") else str(source.type)
        api_endpoint = source.api_endpoint
        auth = source.auth or {}
        schema = source.schema or {}

    if not enabled:
        raise ValueError("内容源已禁用")
    if t == "api":
        return fetch_from_api(
            api_endpoint,
            auth=auth,
            schema=schema,
            timeout=timeout,
        )
    if t == "rss":
        return fetch_from_rss(
            api_endpoint,
            auth=auth,
            schema=schema,
            timeout=timeout,
            limit=limit,
        )
    raise ValueError(f"不支持的内容源类型: {t}")
