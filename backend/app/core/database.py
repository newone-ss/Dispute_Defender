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
    """Initialize all database tables defined on declarative Base with auto-migration."""
    import logging
    import time

    from app.core import models  # noqa: F401 - Register models on Base.metadata

    logger = logging.getLogger(__name__)

    # Auto-migrate legacy disputes schema if present in SQLite
    if engine.dialect.name == "sqlite":
        with engine.connect() as conn:
            cursor = conn.connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='disputes';")
            if cursor.fetchone():
                cursor.execute("PRAGMA table_info(disputes);")
                columns = [row[1] for row in cursor.fetchall()]
                if columns and "amount_paise" not in columns:
                    logger.warning(
                        "Detected legacy disputes table missing 'amount_paise'. Migrating to v3 schema..."
                    )
                    cursor.execute(
                        "SELECT id, dispute_id, payment_id, reason_code, status, amount FROM disputes;"
                    )
                    legacy_rows = cursor.fetchall()
                    cursor.execute("DROP TABLE disputes;")
                    conn.connection.commit()

                    Base.metadata.create_all(bind=engine)

                    if legacy_rows:
                        status_map = {
                            "contested": "AUTO_CONTESTED",
                            "needs_review": "NEEDS_REVIEW",
                            "under_review": "RECEIVED",
                            "accepted": "AUTO_ACCEPTED",
                        }
                        now_str = time.strftime("%Y-%m-%d %H:%M:%S")
                        for row in legacy_rows:
                            _id, d_id, p_id, r_code, st, amt = row
                            new_st = status_map.get(str(st).lower(), "RECEIVED")
                            amt_paise = amt or 0
                            cursor.execute(
                                """
                                INSERT INTO disputes (
                                    id, razorpay_dispute_id, payment_id, idempotency_key,
                                    reason_code, amount_paise, currency, status,
                                    audit_log, created_at, updated_at
                                ) VALUES (?, ?, ?, ?, ?, ?, 'INR', ?, '[]', ?, ?);
                                """,
                                (
                                    _id,
                                    d_id or f"disp_{_id}",
                                    p_id or f"pay_{_id}",
                                    f"{d_id or _id}:{int(time.time())}",
                                    r_code or "product_not_received",
                                    amt_paise,
                                    new_st,
                                    now_str,
                                    now_str,
                                ),
                            )
                        conn.connection.commit()
                        logger.info(
                            f"Successfully migrated {len(legacy_rows)} legacy disputes to v3 schema."
                        )

    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency providing a transactional database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
