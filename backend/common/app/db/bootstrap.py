from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.engine import Engine

from common.app.db.base import Base
from common.app.models import platform  # noqa: F401


def build_engine(database_url: str) -> Engine:
    return create_engine(
        database_url,
        future=True,
        pool_pre_ping=True,
    )


def initialize_database(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS citext"))

    Base.metadata.create_all(bind=engine)
