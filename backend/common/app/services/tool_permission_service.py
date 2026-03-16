"""Resolve agent's allowed tool slugs for permission validation."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from sqlalchemy import select

from common.app.models import Agent
from common.app.models import AgentToolLink
from common.app.models import AgentToolPermission


def get_allowed_tool_slugs(session: Session, agent_id: UUID) -> list[str] | None:
    """
    Get list of tool slugs the agent is allowed to use.
    Sources: AgentToolPermission (tool_slug) + AgentToolLink (Tool.slug).
    Returns None if no permissions configured (allow-all for backward compat).
    Returns [] if agent not found.
    Returns list of slugs if any permissions exist.
    """
    agent = session.scalar(
        select(Agent)
        .options(
            joinedload(Agent.tool_permissions),
            joinedload(Agent.tool_links).joinedload(AgentToolLink.tool),
        )
        .where(Agent.id == agent_id)
    )
    if agent is None:
        return []

    slugs: set[str] = set()
    for perm in agent.tool_permissions or []:
        slugs.add(perm.tool_slug.strip().lower())
    for link in agent.tool_links or []:
        if link.tool and link.is_enabled:
            slugs.add(link.tool.slug.strip().lower())

    if not slugs:
        return None  # No restrictions: allow all
    return sorted(slugs)


def agent_can_use_tool(session: Session, agent_id: UUID, tool_slug: str) -> bool:
    """
    Check if agent is allowed to use the given tool (by slug).
    Returns True if allowed, False if denied.
    """
    allowed = get_allowed_tool_slugs(session, agent_id)
    if allowed is None:
        return True
    return tool_slug.strip().lower() in {s.lower() for s in allowed}
