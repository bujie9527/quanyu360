#!/usr/bin/env python3
"""Seed publish_article_workflow 到首个项目。可在已有数据库上独立运行。"""
from __future__ import annotations

import os
import sys

# 确保 backend 目录在 PYTHONPATH，以便导入 common
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

        existing = session.scalar(
            select(Workflow).where(
                Workflow.project_id == project.id,
                Workflow.slug == "publish_article_workflow",
            )
        )
        if existing:
            print(f"publish_article_workflow already exists (id={existing.id})")
            return 0

        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        wf = Workflow(
            project_id=project.id,
            name="Publish Article Workflow",
            slug="publish_article_workflow",
            version=1,
            status=WorkflowStatus.active,
            trigger_type=WorkflowTriggerType.manual,
            definition={
                "steps": [
                    {"tool": "fetch_content", "id": "fetch_content"},
                    {"tool": "seo.generate_meta", "id": "seo_generate"},
                    {"tool": "wordpress.publish_post", "id": "publish_wordpress"},
                    {"tool": "log_result", "id": "log_result"},
                ],
            },
            published_at=now,
        )
        session.add(wf)
        session.flush()

        steps = [
            WorkflowStep(
                workflow_id=wf.id,
                step_key="fetch_content",
                name="Fetch Content",
                step_type=WorkflowStepType.tool_call,
                sequence=1,
                next_step_key="seo_generate",
                retry_limit=2,
                timeout_seconds=60,
                config={"tool_name": "fetch_content", "action": "fetch", "parameters": {}},
            ),
            WorkflowStep(
                workflow_id=wf.id,
                step_key="seo_generate",
                name="SEO Generate Meta",
                step_type=WorkflowStepType.tool_call,
                sequence=2,
                next_step_key="publish_wordpress",
                retry_limit=2,
                timeout_seconds=120,
                config={"tool_name": "seo_generate_meta", "action": "generate", "parameters": {}},
            ),
            WorkflowStep(
                workflow_id=wf.id,
                step_key="publish_wordpress",
                name="Publish to WordPress",
                step_type=WorkflowStepType.tool_call,
                sequence=3,
                next_step_key="log_result",
                retry_limit=2,
                timeout_seconds=60,
                config={
                    "tool_name": "wordpress_publish_post",
                    "action": "publish",
                    "parameters": {"status": "publish"},
                },
            ),
            WorkflowStep(
                workflow_id=wf.id,
                step_key="log_result",
                name="Log Result",
                step_type=WorkflowStepType.tool_call,
                sequence=4,
                next_step_key=None,
                retry_limit=0,
                timeout_seconds=30,
                config={"tool_name": "log_result", "action": "log", "parameters": {}},
            ),
        ]
        for s in steps:
            session.add(s)

        session.commit()
        print(f"Created publish_article_workflow (id={wf.id})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
