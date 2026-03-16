from __future__ import annotations

import time

from app.core.queue import dequeue_execution
from app.core.runner import run_execution
from app.core.state import load_execution_state


def run_worker(poll_sleep_seconds: float = 0.25) -> None:
    while True:
        execution_id = dequeue_execution()
        if execution_id is None:
            time.sleep(poll_sleep_seconds)
            continue

        state = load_execution_state(execution_id)
        if state is None:
            continue

        workflow_snapshot = state.context.get("workflow_snapshot")
        if not isinstance(workflow_snapshot, dict):
            continue

        run_execution(execution_id, workflow_snapshot)


if __name__ == "__main__":
    run_worker()
