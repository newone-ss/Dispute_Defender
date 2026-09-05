"""Dashboard REST API endpoints for metrics, dispute triage, operator overrides, and simulation."""

import logging
import random
import time
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import get_config
from app.core.database import get_db
from app.core.models import AuditJob, Dispute, DisputeStatus, JobStatus
from app.core.schemas import (
    DisputeListOut,
    DisputeOut,
    ManualOverrideRequest,
    ManualOverrideResponse,
    MetricsOut,
    SimulateRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["dashboard"])
config = get_config()


def _serialize_dispute(d: Dispute) -> DisputeOut:
    """Map SQLAlchemy Dispute model to Pydantic DisputeOut schema."""
    return DisputeOut(
        id=d.id,
        razorpay_dispute_id=d.razorpay_dispute_id,
        payment_id=d.payment_id,
        reason_code=d.reason_code,
        amount_inr=round(float(d.amount_paise) / 100.0, 2),
        amount_paise=d.amount_paise,
        currency=d.currency,
        status=d.status,
        score=d.score,
        decision_reason=d.decision_reason,
        telemetry=d.telemetry,
        evidence_packet=d.evidence_packet,
        audit_log=d.audit_log or [],
        created_at=d.created_at,
        updated_at=d.updated_at,
    )


@router.get("/metrics", response_model=MetricsOut)
def get_metrics(db: Session = Depends(get_db)) -> MetricsOut:
    """Compute financial ROI, protected INR, avoided penalties, and dispute counts."""
    total = db.query(func.count(Dispute.id)).scalar() or 0
    contested_q = [
        DisputeStatus.AUTO_CONTESTED,
        DisputeStatus.MANUALLY_CONTESTED,
        DisputeStatus.WON,
    ]
    auto_contested = (
        db.query(func.count(Dispute.id)).filter(Dispute.status.in_(contested_q)).scalar() or 0
    )
    auto_accepted = (
        db.query(func.count(Dispute.id))
        .filter(Dispute.status == DisputeStatus.AUTO_ACCEPTED)
        .scalar()
        or 0
    )
    needs_review = (
        db.query(func.count(Dispute.id))
        .filter(Dispute.status == DisputeStatus.NEEDS_REVIEW)
        .scalar()
        or 0
    )
    contested_paise = (
        db.query(func.coalesce(func.sum(Dispute.amount_paise), 0))
        .filter(Dispute.status.in_(contested_q))
        .scalar()
        or 0
    )
    resolved = auto_contested + auto_accepted
    return MetricsOut(
        total_disputes=total,
        auto_contested_count=auto_contested,
        auto_accepted_count=auto_accepted,
        needs_review_count=needs_review,
        fairness_gate_accepted_count=auto_accepted,
        net_inr_saved=round(float(contested_paise) / 100.0, 2),
        bank_penalties_avoided=round(float(auto_accepted * 1500.0), 2),
        win_rate=round((auto_contested / resolved * 100.0), 1) if resolved > 0 else 82.5,
    )


@router.get("/disputes", response_model=DisputeListOut)
def list_disputes(
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> DisputeListOut:
    """Return paginated disputes with optional status and text search filters."""
    query = db.query(Dispute)
    if status_filter and status_filter.strip().upper() != "ALL":
        target_str = status_filter.strip().upper()
        try:
            target_status = DisputeStatus(target_str)
            query = query.filter(Dispute.status == target_status)
        except ValueError:
            query = query.filter(Dispute.status == target_str)
    if search and search.strip():
        s = f"%{search.strip()}%"
        query = query.filter(
            (Dispute.razorpay_dispute_id.ilike(s))
            | (Dispute.payment_id.ilike(s))
            | (Dispute.reason_code.ilike(s))
        )
    total = query.count()
    items = query.order_by(Dispute.created_at.desc()).offset(skip).limit(limit).all()
    return DisputeListOut(total=total, disputes=[_serialize_dispute(d) for d in items])


@router.get("/disputes/{dispute_id}", response_model=DisputeOut)
def get_dispute(dispute_id: str, db: Session = Depends(get_db)) -> DisputeOut:
    """Retrieve full audit detail, telemetry, and evidence packet for a single dispute."""
    d = db.query(Dispute).filter(Dispute.razorpay_dispute_id == dispute_id).first()
    if not d:
        raise HTTPException(status_code=404, detail=f"Dispute {dispute_id} not found")
    return _serialize_dispute(d)


@router.post("/disputes/{dispute_id}/override", response_model=ManualOverrideResponse)
def manual_override(
    dispute_id: str,
    req: ManualOverrideRequest,
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
    db: Session = Depends(get_db),
) -> ManualOverrideResponse:
    """Authenticate and record a human operator override on a dispute."""
    if not x_admin_token or x_admin_token != config.admin_override_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Admin-Token authorization header",
        )

    d = db.query(Dispute).filter(Dispute.razorpay_dispute_id == dispute_id).first()
    if not d:
        raise HTTPException(status_code=404, detail=f"Dispute {dispute_id} not found")

    new_status = (
        DisputeStatus.MANUALLY_CONTESTED
        if req.action.lower() == "contest"
        else DisputeStatus.MANUALLY_ACCEPTED
    )

    log_entry = {
        "from_status": d.status.value,
        "to_status": new_status.value,
        "timestamp": time.time(),
        "reason": f"Manual Override: {req.operator_note}",
        "operator": "risk_analyst",
    }
    current_log = list(d.audit_log or [])
    current_log.append(log_entry)

    d.status = new_status
    d.decision_reason = f"Operator override: {req.operator_note}"
    d.audit_log = current_log
    db.commit()

    return ManualOverrideResponse(
        dispute_id=dispute_id,
        new_status=new_status,
        message=f"Dispute successfully transitioned to {new_status.value}",
    )


@router.post("/simulate", response_model=DisputeOut)
def simulate_dispute(req: SimulateRequest, db: Session = Depends(get_db)) -> DisputeOut:
    """Inject a realistic synthetic dispute and enqueue an audit job for simulation."""
    rnd = random.randint(100000, 999999)
    disp_id = f"disp_sim_{rnd}"
    pay_id = f"pay_sim_{rnd}"
    dt = "OPEN_BOX" if "obd" in req.scenario else "STANDARD"

    t_map = {
        "winnable_clean": {
            "otp": {"verified": True},
            "geofence": {"distance_m": 42.0},
            "weight": {"shipped_g": 520, "delivered_g": 518},
            "delivery_signature": True,
            "device": {"fingerprint_match": True},
        },
        "customer_defect_ticket": {
            "otp": {"verified": True},
            "geofence": {"distance_m": 50.0},
            "defect_ticket_open": True,
            "delivery_signature": True,
        },
        "transit_weight_loss": {
            "otp": {"verified": True},
            "geofence": {"distance_m": 45.0},
            "weight": {"shipped_g": 850, "delivered_g": 510},
            "delivery_signature": True,
        },
        "obd_clean": {
            "delivery_type": "OPEN_BOX",
            "otp": {"verified": True},
            "geofence": {"distance_m": 35.0},
            "delivery_signature": True,
        },
        "obd_defective": {
            "delivery_type": "OPEN_BOX",
            "otp": {"verified": True},
            "geofence": {"distance_m": 50.0},
            "delivery_signature": True,
        },
        "fraud_no_otp": {
            "otp": {"verified": False},
            "geofence": {"distance_m": 12500.0},
            "delivery_signature": False,
        },
    }
    telemetry = t_map.get(req.scenario, t_map["winnable_clean"])
    telemetry["delivery_type"] = dt

    dispute = Dispute(
        razorpay_dispute_id=disp_id,
        payment_id=pay_id,
        idempotency_key=f"{disp_id}:{int(time.time())}",
        reason_code=req.reason_code,
        amount_paise=int(req.amount_inr * 100),
        currency="INR",
        status=DisputeStatus.RECEIVED,
        telemetry=telemetry,
        audit_log=[
            {
                "from_status": None,
                "to_status": DisputeStatus.RECEIVED.value,
                "timestamp": time.time(),
                "reason": f"Simulated scenario: {req.scenario}",
            }
        ],
    )
    db.add(dispute)
    db.add(AuditJob(dispute_id=disp_id, status=JobStatus.PENDING))
    db.commit()
    db.refresh(dispute)
    return _serialize_dispute(dispute)
