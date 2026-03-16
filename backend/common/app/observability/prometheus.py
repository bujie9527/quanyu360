from __future__ import annotations

from collections.abc import Mapping

from fastapi import Response

PROMETHEUS_CONTENT_TYPE = "text/plain; version=0.0.4; charset=utf-8"


def build_metrics_response(payload: str) -> Response:
    return Response(content=payload, media_type=PROMETHEUS_CONTENT_TYPE)


def format_metric(
    name: str,
    metric_type: str,
    help_text: str,
    samples: list[tuple[Mapping[str, str], int | float]],
) -> str:
    lines = [
        f"# HELP {name} {help_text}",
        f"# TYPE {name} {metric_type}",
    ]
    for labels, value in samples:
        lines.append(f"{name}{_format_labels(labels)} {value}")
    return "\n".join(lines)


def calculate_quantile(values: list[float], quantile: float) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = min(len(sorted_values) - 1, max(0, int(round((len(sorted_values) - 1) * quantile))))
    return float(sorted_values[index])


def _format_labels(labels: Mapping[str, str]) -> str:
    if not labels:
        return ""
    rendered = ",".join(f'{key}="{_escape_label(value)}"' for key, value in sorted(labels.items()))
    return f"{{{rendered}}}"


def _escape_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def basic_service_metrics(service_name: str) -> str:
    """Minimal metrics for services without analytics."""
    return format_metric(
        "ai_workforce_service_up",
        "gauge",
        "Service availability (1=up).",
        [({"service": service_name}, 1)],
    ) + "\n"
