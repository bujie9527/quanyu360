from __future__ import annotations

import os
import sys

from common.app.db.bootstrap import build_engine
from common.app.db.bootstrap import initialize_database


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL") or os.getenv("PLATFORM_DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL or PLATFORM_DATABASE_URL must be set.")
    return database_url


def main() -> int:
    engine = build_engine(get_database_url())
    initialize_database(engine)
    print("Database schema initialized successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
