"""SQLAlchemy ORM models for Disputes and Courier Telemetry."""

from sqlalchemy import Boolean, Column, Float, Integer, String

from core.database import Base


class Dispute(Base):
    """Dispute tracking chargeback lifecycle states and payment metadata."""

    __tablename__ = "disputes"

    id = Column(Integer, primary_key=True, index=True)
    dispute_id = Column(String, unique=True, index=True, nullable=False)
    payment_id = Column(String, index=True, nullable=True)
    reason_code = Column(String, nullable=True)
    status = Column(String, default="under_review", nullable=False)
    amount = Column(Integer, nullable=True)


class Telemetry(Base):
    """Courier delivery telemetry captured at doorstep to defend disputes."""

    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(String, unique=True, index=True, nullable=False)
    delivery_type = Column(String, default="STANDARD", nullable=True)  # 'OPEN_BOX' or 'STANDARD'
    otp_verified = Column(Boolean, default=False, nullable=False)
    gps_distance_meters = Column(Float, default=0.0, nullable=True)
