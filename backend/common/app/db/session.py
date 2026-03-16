from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from common.app.core.config import ServiceSettings


def create_session_factory(settings: ServiceSettings) -> sessionmaker[Session] | None:
    if not settings.database_url:
        return None

    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        future=True,
    )
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db(session_factory: sessionmaker[Session] | None) -> Generator[Session, None, None]:
    if session_factory is None:
        yield from ()
        return

    session = session_factory()
    try:
        yield session
    finally:
        session.close()
