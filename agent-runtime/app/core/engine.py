"""
Agent Runtime Engine.

Execution flow:
    Task → Planning → Tool Selection → Tool Execution → Result

Components:
    - AgentRunner: Main orchestrator
    - TaskPlanner: Analyzes task, selects tools, produces ExecutionPlan
    - ToolExecutor: Runs planned tool calls, collects results
    - MemoryManager: Session memory + Redis persistence

Structured logging: All components emit JSON logs with stage, agent_id, task_id, duration_ms.
"""
from __future__ import annotations

from app.core.memory_manager import MemoryManager
from app.core.runner import AgentRunner
from app.core.runner import build_execution
from app.core.task_planner import TaskPlanner
from app.core.tool_executor import ToolExecutor

__all__ = [
    "AgentRunner",
    "TaskPlanner",
    "ToolExecutor",
    "MemoryManager",
    "build_execution",
]
