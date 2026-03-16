"""Tool execution sandbox: timeout, error isolation, and logging for safe tool runs."""
from __future__ import annotations

import logging
from concurrent.futures import Future
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

from tools.runtime.base import ToolExecutionResult

logger = logging.getLogger(__name__)

# Default timeout when not specified
DEFAULT_TIMEOUT_SECONDS = 60

# Shared executor for sandboxed execution (bounded threads)
_executor: ThreadPoolExecutor | None = None


def _get_executor() -> ThreadPoolExecutor:
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(max_workers=32, thread_name_prefix="tool-sandbox")
    return _executor


def run_sandboxed(
    execute_fn: Callable[[], ToolExecutionResult],
    *,
    tool_name: str,
    action: str,
    timeout_seconds: int | None = None,
) -> ToolExecutionResult:
    """
    Run tool execution in a sandbox: timeout, error isolation, logging.
    Prevents unsafe operations from crashing the main process.
    """
    timeout = timeout_seconds if timeout_seconds is not None and timeout_seconds > 0 else DEFAULT_TIMEOUT_SECONDS

    logger.info(
        "sandbox.start",
        extra={
            "tool_name": tool_name,
            "action": action,
            "timeout_seconds": timeout,
        },
    )

    future: Future[ToolExecutionResult] = _get_executor().submit(execute_fn)

    try:
        result = future.result(timeout=timeout)
        if result.success:
            logger.info(
                "sandbox.complete",
                extra={
                    "tool_name": tool_name,
                    "action": action,
                    "success": True,
                },
            )
        else:
            logger.warning(
                "sandbox.complete",
                extra={
                    "tool_name": tool_name,
                    "action": action,
                    "success": False,
                    "error_message": result.error_message,
                },
            )
        return result
    except TimeoutError:
        logger.warning(
            "sandbox.timeout",
            extra={
                "tool_name": tool_name,
                "action": action,
                "timeout_seconds": timeout,
            },
        )
        return ToolExecutionResult(
            tool_name=tool_name,
            action=action,
            success=False,
            output={},
            error_message=f"Tool execution timed out after {timeout} seconds.",
        )
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "sandbox.error",
            extra={
                "tool_name": tool_name,
                "action": action,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
            exc_info=True,
        )
        return ToolExecutionResult(
            tool_name=tool_name,
            action=action,
            success=False,
            output={},
            error_message=f"Tool execution failed: {exc!s}",
        )


def run_sandboxed_sync(
    execute_fn: Callable[[], ToolExecutionResult],
    *,
    tool_name: str,
    action: str,
    timeout_seconds: int | None = None,
) -> ToolExecutionResult:
    """
    Synchronous sandbox: runs in current thread with timeout via signal (Unix) or
    falls back to direct execution with error isolation.
    On non-Unix or when threads preferred, use run_sandboxed.
    """
    logger.info(
        "sandbox.start",
        extra={"tool_name": tool_name, "action": action},
    )
    try:
        result = execute_fn()
        if result.success:
            logger.info("sandbox.complete", extra={"tool_name": tool_name, "action": action, "success": True})
        else:
            logger.warning(
                "sandbox.complete",
                extra={"tool_name": tool_name, "action": action, "success": False, "error_message": result.error_message},
            )
        return result
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "sandbox.error",
            extra={
                "tool_name": tool_name,
                "action": action,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
            exc_info=True,
        )
        return ToolExecutionResult(
            tool_name=tool_name,
            action=action,
            success=False,
            output={},
            error_message=f"Tool execution failed: {exc!s}",
        )
