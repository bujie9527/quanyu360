from __future__ import annotations

import json
from typing import Any

from redis import Redis

from app.core.config import get_settings
from app.core.schemas import AnalyticsPoint
from app.core.schemas import RuntimeAnalyticsSummary
from common.app.observability.prometheus import calculate_quantile
from common.app.observability.prometheus import format_metric


def estimate_token_count(*parts: object) -> int:
    text = " ".join(_normalize_part(part) for part in parts if part is not None).strip()
    if not text:
        return 0
    return max(1, int(round(len(text) / 4)))


def record_runtime_execution(
    *,
    status: str,
    provider: str,
    model: str,
    duration_seconds: float,
    prompt_tokens: int,
    completion_tokens: int,
) -> None:
    settings = get_settings()
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    prefix = settings.analytics_key_prefix
    total_tokens = prompt_tokens + completion_tokens
    recent_record = {
        "label": model,
        "status": status,
        "provider": provider,
        "duration_seconds": round(max(duration_seconds, 0.0), 6),
        "prompt_tokens": max(prompt_tokens, 0),
        "completion_tokens": max(completion_tokens, 0),
        "total_tokens": max(total_tokens, 0),
    }

    pipe = client.pipeline()
    pipe.hincrby(f"{prefix}:summary", "runs_total", 1)
    pipe.hincrby(f"{prefix}:summary", f"{status}_runs", 1)
    pipe.hincrbyfloat(f"{prefix}:summary", "duration_seconds_total", max(duration_seconds, 0.0))
    pipe.hincrby(f"{prefix}:summary", "prompt_tokens_total", max(prompt_tokens, 0))
    pipe.hincrby(f"{prefix}:summary", "completion_tokens_total", max(completion_tokens, 0))
    pipe.hincrby(f"{prefix}:summary", "total_tokens_total", max(total_tokens, 0))
    pipe.hincrby(f"{prefix}:providers", provider, 1)
    pipe.lpush(f"{prefix}:recent", json.dumps(recent_record))
    pipe.ltrim(f"{prefix}:recent", 0, 49)
    pipe.execute()


def get_runtime_analytics_summary() -> RuntimeAnalyticsSummary:
    settings = get_settings()
    try:
        client = Redis.from_url(settings.redis_url, decode_responses=True)
        prefix = settings.analytics_key_prefix
        summary = client.hgetall(f"{prefix}:summary")
        providers = client.hgetall(f"{prefix}:providers")
        recent_raw = client.lrange(f"{prefix}:recent", 0, 11)
        recent_records = [json.loads(item) for item in reversed(recent_raw)]
    except Exception:
        summary = {}
        providers = {}
        recent_records = []

    runs_total = _int_value(summary.get("runs_total"))
    successful_runs = _int_value(summary.get("completed_runs"))
    failed_runs = _int_value(summary.get("failed_runs"))
    prompt_tokens_total = _int_value(summary.get("prompt_tokens_total"))
    completion_tokens_total = _int_value(summary.get("completion_tokens_total"))
    total_tokens_total = _int_value(summary.get("total_tokens_total"))
    duration_total = _float_value(summary.get("duration_seconds_total"))
    success_rate = successful_runs / runs_total if runs_total else 0.0
    average_duration = duration_total / runs_total if runs_total else 0.0
    average_tokens = total_tokens_total / runs_total if runs_total else 0.0

    provider_breakdown = [
        AnalyticsPoint(label=provider, value=float(count))
        for provider, count in sorted(providers.items())
    ]
    recent_token_usage = [
        AnalyticsPoint(label=f"Run {index + 1}", value=float(record.get("total_tokens", 0)))
        for index, record in enumerate(recent_records[-6:])
    ]
    execution_time_breakdown = [
        AnalyticsPoint(label=record.get("label", f"Run {index + 1}"), value=float(record.get("duration_seconds", 0.0)))
        for index, record in enumerate(recent_records[-6:])
    ]

    return RuntimeAnalyticsSummary(
        runs_total=runs_total,
        successful_runs=successful_runs,
        failed_runs=failed_runs,
        success_rate=round(success_rate, 6),
        average_execution_time_seconds=round(average_duration, 6),
        prompt_tokens_total=prompt_tokens_total,
        completion_tokens_total=completion_tokens_total,
        total_tokens_total=total_tokens_total,
        average_tokens_per_run=round(average_tokens, 6),
        provider_breakdown=provider_breakdown,
        recent_token_usage=recent_token_usage,
        execution_time_breakdown=execution_time_breakdown,
    )


def render_prometheus_metrics(summary: RuntimeAnalyticsSummary) -> str:
    recent_durations = [point.value for point in summary.execution_time_breakdown]
    p95_duration = calculate_quantile(recent_durations, 0.95)
    payload = [
        format_metric(
            "ai_workforce_agent_runs_total",
            "gauge",
            "Total number of agent runtime runs grouped by outcome.",
            [
                ({"status": "completed"}, summary.successful_runs),
                ({"status": "failed"}, summary.failed_runs),
            ],
        ),
        format_metric(
            "ai_workforce_agent_success_rate",
            "gauge",
            "Ratio of successful agent runtime runs to all runs.",
            [({}, summary.success_rate)],
        ),
        format_metric(
            "ai_workforce_agent_execution_seconds_avg",
            "gauge",
            "Average end-to-end agent runtime execution time in seconds.",
            [({}, summary.average_execution_time_seconds)],
        ),
        format_metric(
            "ai_workforce_agent_execution_seconds_p95",
            "gauge",
            "P95 end-to-end agent runtime execution time in seconds from recent runs.",
            [({}, round(p95_duration, 6))],
        ),
        format_metric(
            "ai_workforce_agent_token_usage_total",
            "gauge",
            "Aggregated token usage observed by the agent runtime.",
            [
                ({"type": "prompt"}, summary.prompt_tokens_total),
                ({"type": "completion"}, summary.completion_tokens_total),
                ({"type": "total"}, summary.total_tokens_total),
            ],
        ),
    ]
    return "\n".join(payload) + "\n"


def _normalize_part(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, sort_keys=True, default=str)
    return str(value)


def _int_value(value: str | None) -> int:
    if value is None or value == "":
        return 0
    return int(float(value))


def _float_value(value: str | None) -> float:
    if value is None or value == "":
        return 0.0
    return float(value)
