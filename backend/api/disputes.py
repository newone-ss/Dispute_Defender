"""Disputes, Metrics, and Telemetry management router for Razorpay Dispute Defender."""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.ai_engine import evaluate_dispute_fairness
from core.database import get_db
from data.models import Dispute, Telemetry

logger = logging.getLogger("disputes")
router = APIRouter(tags=["disputes"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class TelemetryCreate(BaseModel):
    """Payload to register or update courier doorstep telemetry for a payment."""
    payment_id: str
    delivery_type: Optional[str] = "STANDARD"
    otp_verified: bool = True
    gps_distance_meters: Optional[float] = 15.0


class EvaluateDisputeRequest(BaseModel):
    """Payload to trigger LLM dispute fairness assessment."""
    dispute_text: str


# ---------------------------------------------------------------------------
# Metrics Endpoint
# ---------------------------------------------------------------------------
@router.get("/metrics")
def get_metrics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Retrieve financial metrics, dispute breakdown, and protected amounts."""
    total = db.query(func.count(Dispute.id)).scalar() or 0
    contested_count = db.query(func.count(Dispute.id)).filter(Dispute.status == "contested").scalar() or 0
    needs_review_count = db.query(func.count(Dispute.id)).filter(Dispute.status == "needs_review").scalar() or 0
    under_review_count = db.query(func.count(Dispute.id)).filter(Dispute.status == "under_review").scalar() or 0

    total_amount_paise = db.query(func.coalesce(func.sum(Dispute.amount), 0)).scalar() or 0
    contested_amount_paise = (
        db.query(func.coalesce(func.sum(Dispute.amount), 0))
        .filter(Dispute.status == "contested")
        .scalar()
        or 0
    )

    resolved = contested_count + needs_review_count
    win_rate = round((contested_count / resolved * 100.0), 1) if resolved > 0 else 0.0

    return {
        "total_disputes": total,
        "contested_count": contested_count,
        "needs_review_count": needs_review_count,
        "under_review_count": under_review_count,
        "total_amount_inr": round(float(total_amount_paise) / 100.0, 2),
        "protected_inr": round(float(contested_amount_paise) / 100.0, 2),
        "win_rate_percent": win_rate,
    }


# ---------------------------------------------------------------------------
# Disputes Endpoints
# ---------------------------------------------------------------------------
@router.get("/disputes")
def list_disputes(
    status: Optional[str] = Query(None, description="Filter by status (e.g., contested, needs_review)"),
    search: Optional[str] = Query(None, description="Search by dispute_id or payment_id"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Retrieve paginated disputes stored in SQLite database."""
    query = db.query(Dispute)
    if status:
        query = query.filter(Dispute.status == status)
    if search:
        s = f"%{search.strip()}%"
        query = query.filter((Dispute.dispute_id.ilike(s)) | (Dispute.payment_id.ilike(s)))

    total = query.count()
    items = query.order_by(Dispute.id.desc()).offset(skip).limit(limit).all()

    disputes_out = [
        {
            "id": d.id,
            "dispute_id": d.dispute_id,
            "payment_id": d.payment_id,
            "reason_code": d.reason_code,
            "amount_paise": d.amount,
            "amount_inr": round(float(d.amount or 0) / 100.0, 2),
            "status": d.status,
        }
        for d in items
    ]

    return {"total": total, "skip": skip, "limit": limit, "disputes": disputes_out}


@router.get("/disputes/{dispute_id}")
def get_dispute(dispute_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Retrieve full detail for a single dispute, including courier doorstep telemetry."""
    dispute = db.query(Dispute).filter(Dispute.dispute_id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail=f"Dispute '{dispute_id}' not found")

    telemetry = None
    if dispute.payment_id:
        t = db.query(Telemetry).filter(Telemetry.payment_id == dispute.payment_id).first()
        if t:
            telemetry = {
                "delivery_type": t.delivery_type,
                "otp_verified": t.otp_verified,
                "gps_distance_meters": t.gps_distance_meters,
            }

    return {
        "id": dispute.id,
        "dispute_id": dispute.dispute_id,
        "payment_id": dispute.payment_id,
        "reason_code": dispute.reason_code,
        "amount_paise": dispute.amount,
        "amount_inr": round(float(dispute.amount or 0) / 100.0, 2),
        "status": dispute.status,
        "telemetry": telemetry,
    }


# ---------------------------------------------------------------------------
# Telemetry Seeder Endpoint (enables full contestation testing)
# ---------------------------------------------------------------------------
@router.post("/telemetry")
def register_telemetry(payload: TelemetryCreate, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Register or update courier doorstep telemetry for a payment_id."""
    t = db.query(Telemetry).filter(Telemetry.payment_id == payload.payment_id).first()
    if not t:
        t = Telemetry(
            payment_id=payload.payment_id,
            delivery_type=payload.delivery_type,
            otp_verified=payload.otp_verified,
            gps_distance_meters=payload.gps_distance_meters,
        )
        db.add(t)
    else:
        t.delivery_type = payload.delivery_type
        t.otp_verified = payload.otp_verified
        t.gps_distance_meters = payload.gps_distance_meters

    db.commit()
    return {
        "status": "ok",
        "payment_id": payload.payment_id,
        "otp_verified": payload.otp_verified,
        "delivery_type": payload.delivery_type,
        "gps_distance_meters": payload.gps_distance_meters,
    }


# ---------------------------------------------------------------------------
# LLM Fairness Evaluation Endpoint
# ---------------------------------------------------------------------------
@router.post("/evaluate/fairness")
def evaluate_fairness(payload: EvaluateDisputeRequest) -> Dict[str, str]:
    """Invoke the Gemini / OpenRouter AI engine to evaluate dispute fairness."""
    decision = evaluate_dispute_fairness(payload.dispute_text)
    return {
        "dispute_text": payload.dispute_text,
        "decision": decision,
    }
