"""Tool rate limiting: per agent and per tenant. Redis-backed fixed window."""
from __future__ import annotations

from dataclasses import dataclass
from time import time

from redis import Redis


@dataclass(frozen=True)
class RateLimitRule:
    """Limit: max N requests per window_seconds."""

    key: str  # e.g. "facebook:create_post", "tool_calls"
    limit: int
    window_seconds: int


# Built-in rules. Key format: tool_name:action or "tool_calls" for generic.
RATE_LIMIT_RULES: dict[str, RateLimitRule] = {
    "facebook:create_post": RateLimitRule("facebook:create_post", 5, 3600),
    "facebook:comment_post": RateLimitRule("facebook:comment_post", 10, 3600),
    "facebook:send_message": RateLimitRule("facebook:send_message", 20, 3600),
    "tool_calls": RateLimitRule("tool_calls", 20, 60),
}


def _rule_key(rule: RateLimitRule, tenant_id: str | None, agent_id: str | None) -> str:
    tid = tenant_id or "default"
    aid = agent_id or "anonymous"
    return f"ratelimit:{rule.key}:t:{tid}:a:{aid}"


def _window_suffix(rule: RateLimitRule) -> str:
    now = int(time())
    window_start = (now // rule.window_seconds) * rule.window_seconds
    return str(window_start)


def check_tool_rate_limit(
    redis_url: str,
    redis_key_prefix: str,
    tool_name: str,
    action: str,
    *,
    tenant_id: str | None = None,
    agent_id: str | None = None,
) -> tuple[bool, str | None]:
    """
    Check if tool call is allowed. Returns (allowed, error_message).
    If allowed, caller must call consume_tool_rate_limit after the call.
    """
    action_key = f"{tool_name}:{action}"
    rule = RATE_LIMIT_RULES.get(action_key) or RATE_LIMIT_RULES.get("tool_calls")
    if not rule:
        return True, None

    try:
        client = Redis.from_url(redis_url, decode_responses=True)
        prefix = redis_key_prefix or "agent-runtime"
        full_key = f"{prefix}:{_rule_key(rule, tenant_id, agent_id)}:{_window_suffix(rule)}"
        current = client.get(full_key) or "0"
        count = int(current)
        if count >= rule.limit:
            return False, (
                f"Rate limit exceeded: {rule.key} max {rule.limit} per "
                f"{rule.window_seconds}s (current: {count})"
            )
        return True, None
    except Exception:
        return True, None  # Fail open on Redis errors


def consume_tool_rate_limit(
    redis_url: str,
    redis_key_prefix: str,
    tool_name: str,
    action: str,
    *,
    tenant_id: str | None = None,
    agent_id: str | None = None,
) -> None:
    """Increment rate limit counter. Call after check passed (and tool was attempted)."""
    action_key = f"{tool_name}:{action}"
    rule = RATE_LIMIT_RULES.get(action_key) or RATE_LIMIT_RULES.get("tool_calls")
    if not rule:
        return

    try:
        client = Redis.from_url(redis_url, decode_responses=True)
        prefix = redis_key_prefix or "agent-runtime"
        full_key = f"{prefix}:{_rule_key(rule, tenant_id, agent_id)}:{_window_suffix(rule)}"
        pipe = client.pipeline()
        pipe.incr(full_key)
        pipe.expire(full_key, rule.window_seconds + 60)
        pipe.execute()
    except Exception:
        pass
