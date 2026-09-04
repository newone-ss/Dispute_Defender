"""SQLAlchemy 2.0 typed ORM models for disputes and durable queue jobs."""

import enum
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, String, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DisputeStatus(str, enum.Enum):
    """Lifecycle states for a chargeback dispute."""

    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    AUTO_CONTESTED = "AUTO_CONTESTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    AUTO_ACCEPTED = "AUTO_ACCEPTED"
    MANUALLY_CONTESTED = "MANUALLY_CONTESTED"
    MANUALLY_ACCEPTED = "MANUALLY_ACCEPTED"
    WON = "WON"
    LOST = "LOST"


class JobStatus(str, enum.Enum):
    """Execution status for durable background audit jobs."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"


class Dispute(Base):
    """Core dispute record capturing Razorpay chargebacks and telemetry state."""

    __tablename__ = "disputes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    razorpay_dispute_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    payment_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    idempotency_key: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=False
    )
    reason_code: Mapped[str] = mapped_column(String(64), nullable=False)
    amount_paise: Mapped[int] = mapped_column(nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    status: Mapped[DisputeStatus] = mapped_column(
        SAEnum(DisputeStatus), default=DisputeStatus.RECEIVED, index=True, nullable=False
    )
    score: Mapped[Optional[int]] = mapped_column(nullable=True)
    decision_reason: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    telemetry: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    evidence_packet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    audit_log: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)

    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now(), nullable=False
    )


class AuditJob(Base):
    """Durable queue job table managing reliable, asynchronous dispute evaluations."""

    __tablename__ = "audit_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dispute_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        SAEnum(JobStatus), default=JobStatus.PENDING, index=True, nullable=False
    )
    attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    leased_until: Mapped[Optional[datetime]] = mapped_column(nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now(), nullable=False
    )
