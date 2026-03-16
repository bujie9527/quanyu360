"""Centralized structured logging. Events: task_start, task_finish, agent_execution, tool_execution, error."""
from __future__ import annotations

import logging
from typing import Any

import structlog


# Event types for structured log correlation
EVENT_TASK_START = "task_start"
EVENT_TASK_FINISH = "task_finish"
EVENT_AGENT_EXECUTION = "agent_execution"
EVENT_TOOL_EXECUTION = "tool_execution"
EVENT_ERROR = "error"


def configure_logging(service_name: str) -> None:
    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    structlog.get_logger(service_name).info(
        "logging_configured",
        service=service_name,
    )


def log_event(
    service_name: str,
    event: str,
    *,
    level: str = "info",
    message: str = "",
    **kwargs: Any,
) -> None:
    """
    Emit a structured log event. Use EVENT_* constants for event.
    All kwargs are included in the JSON output for correlation.
    """
    logger = structlog.get_logger(service_name)
    log_fn = getattr(logger, level, logger.info)
    log_fn(event, message=message, service=service_name, **kwargs)
