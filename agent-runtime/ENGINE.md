# Agent Runtime Engine

## Execution Flow

```
Task → Planning → Tool Selection → Tool Execution → Result
```

1. **Task** – Request received with agent_id, task_id, task payload
2. **Planning** – TaskPlanner analyzes the task and produces an ExecutionPlan (steps + tool_calls)
3. **Tool Selection** – Part of planning; LLM/heuristic selects which tools to invoke
4. **Tool Execution** – ToolExecutor runs each planned tool call and collects results
5. **Result** – LLM adapter synthesizes final response from tool outputs

## Components

| Component | Responsibility | Location |
|-----------|----------------|----------|
| **AgentRunner** | Main orchestrator; wires flow and returns AgentExecutionResult | `app/core/runner.py` |
| **TaskPlanner** | Plans task, selects tools, produces ExecutionPlan | `app/core/task_planner.py` |
| **ToolExecutor** | Executes planned tool calls, returns structured results | `app/core/tool_executor.py` |
| **MemoryManager** | Session memory (create_session) + Redis persistence (persist, load) | `app/core/memory_manager.py` |

## Structured Logging

All components emit JSON logs (structlog) with:

- `stage` – Current phase (e.g. `task_received`, `planning_start`, `tool_execution_complete`)
- `agent_id`, `task_id` – Execution context
- `duration_ms` – Phase or call duration when applicable
- `component` – `agent-runner`, `task-planner`, `tool-executor`, `memory-manager`

Log entries are also captured in `AgentExecutionResult.logs` for inspection and debugging.

## Usage

```python
from app.core.runner import build_execution
from app.core.schemas import AgentRunRequest

request = AgentRunRequest(
    agent_id="...",
    task_id="...",
    task=RuntimeTaskPayload(title="...", description="...", input_payload={}),
)
result = build_execution(request)
```
