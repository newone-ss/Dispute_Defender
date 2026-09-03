"""SQLAlchemy ORM models for Dispute Defender.

Stores core dispute records, status flags, scores, raw courier telemetry,
scanned manifest OCR data, and compiled NPCI UDIR evidence packets.
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Enum as SAEnum, Boolean
from sqlalchemy.sql import func
import enum
from core.database import Base


class DisputeStatus(str, enum.Enum):
    """Lifecycle states for a dispute."""
    RECEIVED = "RECEIVED"                       # Webhook received, not yet processed
    PROCESSING = "PROCESSING"                   # Background task is running audit
    AUTO_CONTESTED = "AUTO_CONTESTED"           # Score > 80 → auto-contest submitted to Razorpay
    NEEDS_REVIEW = "NEEDS_REVIEW"               # Score 40-80 → human review required
    AUTO_ACCEPTED = "AUTO_ACCEPTED"             # Score < 40 or Fairness Gate triggered (defect/loss)
    MANUALLY_CONTESTED = "MANUALLY_CONTESTED"   # Human override → contest submitted
    WON = "WON"                                 # Dispute resolved in merchant's favor
    LOST = "LOST"                               # Dispute resolved against merchant


class Dispute(Base):
    """Core dispute record — one row per Razorpay chargeback event."""

    __tablename__ = "disputes"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # --- Razorpay identifiers ---
    dispute_id = Column(String(64), unique=True, nullable=False, index=True)
    payment_id = Column(String(64), nullable=True, index=True)
    order_id = Column(String(64), nullable=True)

    # --- Core state ---
    status = Column(
        SAEnum(DisputeStatus),
        nullable=False,
        default=DisputeStatus.RECEIVED,
        index=True,
    )
    reason_code = Column(String(64), nullable=True)
    amount = Column(Float, nullable=False, default=0.0)          # In INR
    confidence_score = Column(Float, nullable=True)               # 0.0 – 100.0

    # --- Telemetry evaluation breakdown ---
    otp_verified = Column(Boolean, nullable=True)
    geofence_distance_km = Column(Float, nullable=True)
    shipped_weight_g = Column(Float, nullable=True)
    delivered_weight_g = Column(Float, nullable=True)
    weight_loss_g = Column(Float, nullable=True)
    defect_ticket_open = Column(Boolean, default=False)
    fairness_gate_triggered = Column(Boolean, default=False)
    fairness_reason = Column(String(255), nullable=True)

    # --- Evidence & OCR ---
    evidence_text = Column(Text, nullable=True)                   # Compiled NPCI UDIR markdown packet
    document_id = Column(String(64), nullable=True)               # Razorpay doc_id from /v1/documents
    ocr_manifest_json = Column(Text, nullable=True)               # Parsed manifest OCR data
    raw_telemetry = Column(Text, nullable=True)                   # Full raw JSON payload

    # --- Timestamps ---
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return (
            f"<Dispute(id={self.id}, dispute_id='{self.dispute_id}', "
            f"status={self.status}, score={self.confidence_score})>"
        )
