"""LLM 客户端，供 SEO 工具生成内容。使用 OpenAI 兼容 API。"""
from __future__ import annotations

import json
import os
import re
from typing import Any

import httpx


def _get_config() -> tuple[str | None, str, str, float]:
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("CLAUDE_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.environ.get("SEO_LLM_MODEL", "gpt-4.1-mini")
    timeout = float(os.environ.get("LLM_REQUEST_TIMEOUT_SECONDS", "30"))
    return api_key, base_url, model, timeout


def llm_generate(
    system_prompt: str,
    user_prompt: str,
    *,
    model: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 1024,
) -> str:
    """
    调用 LLM 生成内容。返回生成文本。
    若无 API Key 则抛出 RuntimeError。
    """
    api_key, base_url, default_model, timeout = _get_config()
    if not api_key:
        raise RuntimeError("SEO 工具需要配置 OPENAI_API_KEY 或 CLAUDE_API_KEY")

    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model or default_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    with httpx.Client(timeout=timeout) as client:
        resp = client.post(url, json=payload, headers=headers)

    if resp.status_code >= 400:
        raise RuntimeError(f"LLM 请求失败: HTTP {resp.status_code}")

    data = resp.json()
    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError("LLM 返回空结果")
    content = choices[0].get("message", {}).get("content", "")
    return (content or "").strip()


def llm_generate_json(
    system_prompt: str,
    user_prompt: str,
    *,
    model: str | None = None,
) -> dict[str, Any] | list[Any]:
    """调用 LLM 生成 JSON，自动解析并返回。"""
    raw = llm_generate(
        system_prompt + "\nRespond with ONLY valid JSON, no markdown or extra text.",
        user_prompt,
        model=model,
        temperature=0.2,
    )
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```\s*$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"LLM 返回无效 JSON: {e}") from e
