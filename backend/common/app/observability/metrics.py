"""Centralized metric names and helpers for Prometheus metrics."""
from __future__ import annotations

# Task metrics (task-service)
METRIC_TASKS_EXECUTED_TOTAL = "ai_workforce_tasks_executed_total"
METRIC_TASK_SUCCESS_RATE = "ai_workforce_task_success_rate"
METRIC_TASK_EXECUTION_SECONDS_AVG = "ai_workforce_task_execution_seconds_avg"
METRIC_TASK_EXECUTION_SECONDS_P95 = "ai_workforce_task_execution_seconds_p95"

# Agent metrics (agent-runtime)
METRIC_AGENT_RUNS_TOTAL = "ai_workforce_agent_runs_total"
METRIC_AGENT_SUCCESS_RATE = "ai_workforce_agent_success_rate"
METRIC_AGENT_EXECUTION_SECONDS_AVG = "ai_workforce_agent_execution_seconds_avg"
METRIC_AGENT_EXECUTION_SECONDS_P95 = "ai_workforce_agent_execution_seconds_p95"
METRIC_AGENT_TOKEN_USAGE_TOTAL = "ai_workforce_agent_token_usage_total"

# Workflow metrics (workflow-engine)
METRIC_WORKFLOW_EXECUTIONS_TOTAL = "ai_workforce_workflow_executions_total"
METRIC_WORKFLOW_SUCCESS_RATE = "ai_workforce_workflow_success_rate"
