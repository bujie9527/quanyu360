from __future__ import annotations

import os
import sys
import traceback

from sqlalchemy import text
from sqlalchemy.orm import Session

from common.app.db.bootstrap import build_engine
from common.app.db.bootstrap import initialize_database
from common.app.db.seed import seed_agent_templates
from common.app.db.seed import seed_auth_only


def _get_database_url() -> str:
    url = os.getenv("DATABASE_URL") or os.getenv("PLATFORM_DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL or PLATFORM_DATABASE_URL must be set.")
    return url


def _ensure_tasks_team_id(engine) -> None:
    """Add team_id to tasks if missing (migration 20260309_0008 for task_db)."""
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS team_id UUID NULL"))
            print("Ensured tasks.team_id exists.")
    except Exception as e:
        print(f"Note: could not add team_id to tasks: {e}")


def main() -> int:
    try:
        database_url = _get_database_url()
        engine = build_engine(database_url)
        initialize_database(engine)
        print("Initialized schema for single database.")

        _ensure_tasks_team_id(engine)

        with Session(engine) as session:
            seed_auth_only(session)
        print("Seeded auth data (tenant, users).")

        with Session(engine) as session:
            seed_agent_templates(session)
        print("Seeded agent templates (WordPress Builder, Site Operator, Facebook Operator).")

        print("Database initialization completed.")
        return 0
    except Exception as e:
        print(f"FATAL: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
