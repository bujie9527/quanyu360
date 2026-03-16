"""Schema 映射工具：从原始数据按 schema 提取 title/content/tags。"""
from __future__ import annotations

from typing import Any


def _get_by_path(obj: Any, path: str) -> Any:
    """按点分路径取值，如 'data.headline' 或 'items[0].title'。"""
    if not path or not obj:
        return None
    parts = path.replace("]", "").replace("[", ".").split(".")
    cur = obj
    for p in parts:
        if not p:
            continue
        if isinstance(cur, dict):
            cur = cur.get(p)
        elif isinstance(cur, list):
            try:
                cur = cur[int(p)]
            except (ValueError, IndexError):
                return None
        else:
            return None
    return cur


def _to_string(val: Any) -> str:
    if val is None:
        return ""
    if isinstance(val, str):
        return val
    if isinstance(val, dict):
        return val.get("raw", val.get("rendered", str(val)))
    return str(val)


def _to_tags(val: Any) -> list[str]:
    if val is None:
        return []
    if isinstance(val, list):
        out = []
        for v in val:
            if isinstance(v, str):
                out.append(v)
            elif isinstance(v, dict):
                out.append(v.get("name", v.get("slug", str(v))))
            else:
                out.append(str(v))
        return out
    if isinstance(val, str):
        return [val] if val else []
    return [str(val)]


def apply_schema(data: Any, schema: dict[str, Any] | None) -> dict[str, Any]:
    """
    根据 schema 从原始数据提取 title、content、tags。
    schema 格式: {"title": "path.to.field", "content": "...", "tags": "..."}
    或默认键: title, content, tags 直接对应字段名。
    """
    schema = schema or {}
    title_path = schema.get("title", "title")
    content_path = schema.get("content", "content")
    tags_path = schema.get("tags", "tags")

    title = _get_by_path(data, title_path) if isinstance(title_path, str) else None
    content = _get_by_path(data, content_path) if isinstance(content_path, str) else None
    tags = _get_by_path(data, tags_path) if isinstance(tags_path, str) else None

    return {
        "title": _to_string(title),
        "content": _to_string(content),
        "tags": _to_tags(tags),
    }
