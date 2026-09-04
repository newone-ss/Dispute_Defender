"""SQLAlchemy 2.0 database engine and session dependency.

Configures SQLite with Write-Ahead Logging (WAL) and enforces foreign keys.
Provides a context-managed session dependency ensuring sessions never leak.
"""

import os
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import get_config

config = get_config()

# Ensure local SQLite directory exists if file-based
db_url = config.database_url
if db_url.startswith("sqlite:///"):
    sqlite_file = db_url.replace("sqlite:///", "")
    resolved_path = config.resolve_path(sqlite_file)
    os.makedirs(resolved_path.parent, exist_ok=True)
    connect_args = {"check_same_thread": False}
else:
    connect_args = {}

engine = create_engine(db_url, connect_args=connect_args)


# Enable SQLite WAL mode and foreign key enforcement on every new connection
@event.listens_for(engine, "connect")
def configure_sqlite_pragmas(dbapi_connection, connection_record) -> None:
    """Enforce SQLite WAL mode and referential integrity."""
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA foreign_keys=ON;")
    except Exception:
        pass
    finally:
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db() -> None:
    """Initialize all database tables defined on declarative Base."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency providing a transactional database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
