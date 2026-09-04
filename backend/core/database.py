"""Database configuration and session lifecycle management using SQLAlchemy.

Connects to a local SQLite database and exposes dependency session providers.
"""

import os
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Ensure the SQLite storage directory exists
DB_DIR = os.path.join(".", "data", "mock_db")
os.makedirs(DB_DIR, exist_ok=True)

DATABASE_URL = "sqlite:///./data/mock_db/disputes.db"

# Create engine with check_same_thread=False for multithreaded FastAPI background workers
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def configure_sqlite(dbapi_connection, connection_record) -> None:
    """Enable SQLite WAL mode and foreign key constraints for safe concurrency."""
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


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a clean database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
