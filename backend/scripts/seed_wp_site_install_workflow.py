#!/usr/bin/env python3
"""Seed WordPress install workflow (SSH + WP-CLI)."""
from __future__ import annotations

import os
import sys

_script_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(_script_dir)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from sqlalchemy import select
from sqlalchemy.orm import Session

from common.app.db.bootstrap import build_engine
from common.app.models import Project
from common.app.models import Workflow
from common.app.models import WorkflowStatus
from common.app.models import WorkflowStep
from common.app.models import WorkflowStepType
from common.app.models import WorkflowTriggerType


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL") or os.getenv("PLATFORM_DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL or PLATFORM_DATABASE_URL must be set.")
    return database_url


def main() -> int:
    engine = build_engine(get_database_url())
    with Session(engine) as session:
        project = session.scalar(select(Project).limit(1))
        if not project:
            print("No project found. Run seed_data.py first.")
            return 1

        slug = "wp_site_install_workflow"
        existing = session.scalar(select(Workflow).where(Workflow.project_id == project.id, Workflow.slug == slug))
        if existing:
            print(f"{slug} already exists (id={existing.id})")
            return 0

        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        wf = Workflow(
            project_id=project.id,
            name="WordPress Site Install Workflow",
            slug=slug,
            version=1,
            status=WorkflowStatus.active,
            trigger_type=WorkflowTriggerType.manual,
            definition={"entrypoint": "create_db"},
            published_at=now,
        )
        session.add(wf)
        session.flush()

        steps = [
            ("create_db", "Create DB", "download_wp", {"tool_name": "wpcli", "action": "create_db", "parameters": {}}),
            ("download_wp", "Download WordPress", "config_wp", {"tool_name": "wpcli", "action": "download_core", "parameters": {}}),
            ("config_wp", "Create WP Config", "install_wp", {"tool_name": "wpcli", "action": "create_config", "parameters": {}}),
            ("install_wp", "Install WordPress", "create_api_creds", {"tool_name": "wpcli", "action": "core_install", "parameters": {}}),
            ("create_api_creds", "Create API Credentials", "activate_site", {"tool_name": "wpcli", "action": "create_app_password", "parameters": {}}),
            ("activate_site", "Activate Site", "verify_api", {"tool_name": "wpcli", "action": "update_site_credentials", "parameters": {}}),
            ("verify_api", "Verify REST API", "log_result", {"tool_name": "wordpress_get_posts", "action": "fetch", "parameters": {}}),
            ("log_result", "Log Result", None, {"tool_name": "log_result", "action": "log", "parameters": {}}),
        ]
        for idx, (step_key, name, next_step, config) in enumerate(steps, start=1):
            session.add(
                WorkflowStep(
                    workflow_id=wf.id,
                    step_key=step_key,
                    name=name,
                    step_type=WorkflowStepType.tool_call,
                    sequence=idx,
                    next_step_key=next_step,
                    retry_limit=1,
                    timeout_seconds=180,
                    config=config,
                )
            )

        session.commit()
        print(f"Created {slug} (id={wf.id})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
