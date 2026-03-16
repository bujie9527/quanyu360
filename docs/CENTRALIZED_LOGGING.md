# Centralized Structured Logging

## Event Types

| Event | Description | Emitted By |
|-------|-------------|------------|
| `task_start` | Task execution started | task-service worker |
| `task_finish` | Task execution completed/failed | task-service worker |
| `agent_execution` | Agent run started/finished | agent-runtime runner, workflow-engine agent_node |
| `tool_execution` | Tool call started/finished | agent-runtime tool_executor, workflow-engine tool_node |
| `error` | Error occurred | All services |

## Format

All logs are JSON (structlog). Each event includes:

- `event`: Event type
- `service`: Service name (e.g. `agent-runtime`, `task-service`)
- `timestamp`: ISO 8601
- `message`: Human-readable message
- Context fields: `task_id`, `agent_id`, `tool_name`, `action`, `duration_ms`, etc.

## Example

```json
{
  "event": "task_start",
  "service": "task-service",
  "timestamp": "2025-03-08T12:00:00.000000Z",
  "message": "Task execution started",
  "task_id": "uuid",
  "agent_id": "uuid",
  "project_id": "uuid"
}
```

## Configuration

- `common.app.core.logging.configure_logging(service_name)` – Configure structlog with JSON output
- `common.app.core.logging.log_event(service_name, event, level="info", message="", **kwargs)` – Emit structured event
