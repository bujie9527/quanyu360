"""
Agent Memory System: short-term (Redis) + long-term (Qdrant).

Features:
- Store conversations (short-term + optional long-term)
- Retrieve context (recent turns + relevant memories)
- Update memory after tasks (persist to long-term)
"""
from __future__ import annotations

from datetime import datetime
from datetime import timezone
from typing import Any

import structlog

from app.core.config import get_settings
from app.core.long_term_memory import LongTermMemory
from app.core.schemas import AgentExecutionResult
from app.core.schemas import ConversationTurn
from app.core.schemas import MemoryContext
from app.core.short_term_memory import ShortTermMemory


class AgentMemorySystem:
    """Unified memory: short-term (Redis) for recent conversations, long-term (Qdrant) for semantic context."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.logger = structlog.get_logger(self.settings.service_name).bind(component="agent-memory")
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory()

    def store_conversations(
        self,
        agent_id: str,
        turns: list[ConversationTurn],
        task_id: str | None = None,
        persist_to_long_term: bool = False,
    ) -> bool:
        """Store conversation turns. Always to short-term; optionally to long-term."""
        if not turns:
            return True
        ok = self.short_term.store_conversation(agent_id, turns, task_id)
        if ok and persist_to_long_term:
            docs = [f"{t.role}: {t.content}" for t in turns]
            meta = [
                {
                    "role": t.role,
                    "task_id": t.task_id,
                    "timestamp": t.timestamp.isoformat() if hasattr(t.timestamp, "isoformat") else str(t.timestamp),
                }
                for t in turns
            ]
            self.long_term.store_memories(agent_id, docs, meta, task_id)
        return ok

    def retrieve_context(
        self,
        agent_id: str,
        query: str | None = None,
        task_id: str | None = None,
        recent_limit: int | None = None,
        long_term_limit: int | None = None,
    ) -> MemoryContext:
        """Retrieve context: recent turns from Redis + relevant memories from Qdrant."""
        recent_turns = self.short_term.retrieve_context(agent_id, task_id, recent_limit)
        relevant_memories: list[dict[str, Any]] = []
        if query and query.strip():
            relevant_memories = self.long_term.retrieve_context(
                agent_id, query, long_term_limit, task_id
            )
        return MemoryContext(
            recent_turns=recent_turns,
            relevant_memories=relevant_memories,
        )

    def update_after_task(
        self,
        agent_id: str,
        task_id: str,
        execution_result: AgentExecutionResult,
    ) -> bool:
        """
        Update memory after task completion.
        Persists execution summary and key exchanges to long-term memory.
        """
        try:
            turns: list[ConversationTurn] = []
            for entry in execution_result.memory:
                ts = entry.timestamp if hasattr(entry.timestamp, "isoformat") else datetime.now(timezone.utc)
                turns.append(
                    ConversationTurn(
                        role=entry.role,
                        content=entry.content,
                        timestamp=ts,
                        task_id=task_id,
                        metadata=entry.metadata,
                    )
                )
            self.short_term.store_conversation(agent_id, turns, task_id)

            summary_parts = [
                f"Task: {execution_result.agent_id}/{task_id}",
                f"Status: {execution_result.status}",
                f"Plan: {execution_result.plan.summary}",
            ]
            if execution_result.result.get("content"):
                summary_parts.append(f"Result: {execution_result.result['content'][:500]}")
            summary = " | ".join(summary_parts)
            self.long_term.store_memories(
                agent_id,
                [summary],
                metadata=[{"task_id": task_id, "status": execution_result.status}],
                task_id=task_id,
            )
            self.logger.info(
                "Memory updated after task.",
                agent_id=agent_id,
                task_id=task_id,
                stage="memory_update",
            )
            return True
        except Exception as exc:
            self.logger.warning(
                "Failed to update memory after task.",
                agent_id=agent_id,
                task_id=task_id,
                error=str(exc),
                stage="memory_update",
            )
            return False
