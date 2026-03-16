# Metrics System

## Metrics Exposed

| Metric | Name | Source |
|--------|------|--------|
| **Tasks executed** | `ai_workforce_tasks_executed_total` | task-service |
| **Task success rate** | `ai_workforce_task_success_rate` (0–1) | task-service |
| **Agent execution time** | `ai_workforce_agent_execution_seconds_avg`, `_p95` | agent-runtime |
| **Token usage** | `ai_workforce_agent_token_usage_total{type="prompt|completion|total"}` | agent-runtime |
| **Workflow executions** | `ai_workforce_workflow_executions_total` | workflow-engine |
| **Workflow success rate** | `ai_workforce_workflow_success_rate` (0–1) | workflow-engine |

## Endpoints

### Unified metrics (gateway)

```
GET /api/metrics
GET /api/v1/metrics  # alias, proxied via /api/{path}
```

Aggregated Prometheus metrics from task-service, agent-runtime, and workflow-engine. Single scrape target for platform-wide metrics.

### Per-service metrics

| Service | Endpoint |
|---------|----------|
| task-service | `GET /metrics` |
| agent-runtime | `GET /metrics` |
| workflow-engine | `GET /metrics` |
| api-gateway | `GET /api/metrics` (aggregated) |

### JSON analytics summaries

| Service | Endpoint |
|---------|----------|
| task-service | `GET /tasks/analytics` |
| agent-runtime | `GET /api/v1/analytics/summary` |

## Prometheus scrape config

```yaml
scrape_configs:
  - job_name: "ai-workforce"
    static_configs:
      - targets: ["api-gateway:8300"]
    metrics_path: /api/metrics
```

Or scrape individual services:

```yaml
  - job_name: "task-service"
    static_configs:
      - targets: ["task-service:8004"]
    metrics_path: /metrics
  - job_name: "agent-runtime"
    static_configs:
      - targets: ["agent-runtime:8200"]
    metrics_path: /metrics
```
