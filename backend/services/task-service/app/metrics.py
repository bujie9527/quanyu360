from __future__ import annotations

from app.schemas.task_schemas import TaskAnalyticsSummaryResponse
from common.app.observability.prometheus import format_metric

def render_prometheus_metrics(summary: TaskAnalyticsSummaryResponse) -> str:
    payload = [
        format_metric(
            "ai_workforce_tasks_executed_total",
            "gauge",
            "Total number of recorded task execution attempts across all tasks.",
            [({}, summary.tasks_executed)],
        ),
        format_metric(
            "ai_workforce_task_success_rate",
            "gauge",
            "Ratio of successful task executions to finalized executions.",
            [({}, summary.agent_success_rate)],
        ),
        format_metric(
            "ai_workforce_task_execution_seconds_avg",
            "gauge",
            "Average task execution time in seconds.",
            [({}, summary.average_execution_time_seconds)],
        ),
        format_metric(
            "ai_workforce_task_execution_seconds_p95",
            "gauge",
            "P95 task execution time in seconds.",
            [({}, summary.p95_execution_time_seconds)],
        ),
        format_metric(
            "ai_workforce_tasks_status_total",
            "gauge",
            "Current number of tasks grouped by status.",
            [({"status": point.label.lower().replace(" ", "_")}, point.value) for point in summary.status_breakdown],
        ),
    ]
    return "\n".join(payload) + "\n"
