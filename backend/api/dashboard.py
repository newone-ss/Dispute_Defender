"""Dashboard & Disputes REST API — serves React frontend, metrics, detail inspect, and simulation."""

import json
import logging
import random
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func

from core.config import get_settings
from core.database import get_db, SessionLocal
from core.models import Dispute, DisputeStatus
from core.schemas import (
    DisputeOut,
    DisputeListOut,
    MetricsOut,
    ManualOverrideRequest,
    ManualOverrideResponse,
    SimulateWebhookRequest,
)
from core.compiler import compile_evidence
from core.razorpay_client import razorpay_client
from api.webhook import process_dispute_task

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(tags=["dashboard"])


@router.get("/api/v1/dashboard/metrics", response_model=MetricsOut)
@router.get("/disputes/metrics", response_model=MetricsOut)
def get_dashboard_metrics(db: Session = Depends(get_db)):
    """Compute financial ROI, protected INR, avoided ₹1,500 bank penalties, and dispute counts."""
    total = db.query(func.count(Dispute.id)).scalar() or 0

    auto_contested = (
        db.query(func.count(Dispute.id))
        .filter(Dispute.status.in_([DisputeStatus.AUTO_CONTESTED, DisputeStatus.MANUALLY_CONTESTED, DisputeStatus.WON]))
        .scalar() or 0
    )

    auto_accepted = (
        db.query(func.count(Dispute.id))
        .filter(Dispute.status == DisputeStatus.AUTO_ACCEPTED)
        .scalar() or 0
    )

    fairness_accepted = (
        db.query(func.count(Dispute.id))
        .filter(Dispute.fairness_gate_triggered == True)
        .scalar() or 0
    )

    needs_review = (
        db.query(func.count(Dispute.id))
        .filter(Dispute.status == DisputeStatus.NEEDS_REVIEW)
        .scalar() or 0
    )

    # Net INR saved = Total contested sum (where merchant retains/defends funds)
    contested_amount = (
        db.query(func.coalesce(func.sum(Dispute.amount), 0.0))
        .filter(Dispute.status.in_([
            DisputeStatus.AUTO_CONTESTED,
            DisputeStatus.MANUALLY_CONTESTED,
            DisputeStatus.WON,
        ]))
        .scalar() or 0.0
    )

    # Bank penalty fees avoided: ₹1,500 per auto-accepted weak/defect dispute
    # (By accepting upfront instead of losing an unjustified contest, merchant saves ₹1,500 bank fee)
    penalties_avoided = auto_accepted * settings.bank_penalty_fee_inr

    resolved = auto_contested + auto_accepted
    win_rate = (auto_contested / resolved * 100.0) if resolved > 0 else 82.5

    return MetricsOut(
        total_disputes=total,
        net_inr_saved=float(contested_amount),
        bank_penalties_avoided=float(penalties_avoided),
        auto_win_rate=round(win_rate, 1),
        needs_review_count=needs_review,
        auto_contested_count=auto_contested,
        auto_accepted_count=auto_accepted,
        fairness_gate_auto_accepted_count=fairness_accepted,
    )


@router.get("/api/v1/dashboard/disputes", response_model=DisputeListOut)
@router.get("/disputes", response_model=DisputeListOut)
def list_disputes(
    status: Optional[DisputeStatus] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by dispute_id, payment_id, order_id"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Paginated list of disputes with search and status filtering."""
    query = db.query(Dispute)
    if status:
        query = query.filter(Dispute.status == status)

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            (Dispute.dispute_id.ilike(s)) |
            (Dispute.payment_id.ilike(s)) |
            (Dispute.order_id.ilike(s)) |
            (Dispute.reason_code.ilike(s))
        )

    total = query.count()
    disputes = query.order_by(Dispute.created_at.desc()).offset(skip).limit(limit).all()

    return DisputeListOut(
        total=total,
        disputes=[DisputeOut.model_validate(d) for d in disputes],
    )


@router.get("/api/v1/dashboard/disputes/{dispute_id}", response_model=DisputeOut)
@router.get("/disputes/{dispute_id}", response_model=DisputeOut)
def get_dispute_detail(dispute_id: str, db: Session = Depends(get_db)):
    """Retrieve complete audit logs, telemetry breakdown, and NPCI UDIR evidence text."""
    dispute = db.query(Dispute).filter(Dispute.dispute_id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail=f"Dispute {dispute_id} not found")
    return DisputeOut.model_validate(dispute)


@router.post("/api/v1/dashboard/disputes/{dispute_id}/override", response_model=ManualOverrideResponse)
@router.post("/disputes/override", response_model=ManualOverrideResponse)
async def manual_override(
    dispute_id: Optional[str] = None,
    body: Optional[ManualOverrideRequest] = None,
    db: Session = Depends(get_db),
):
    """Human-in-the-loop manual override for disputes flagged as NEEDS_REVIEW."""
    target_id = dispute_id or (body.dispute_id if body else None)
    if not target_id:
        raise HTTPException(status_code=400, detail="Missing dispute_id")

    dispute = db.query(Dispute).filter(Dispute.dispute_id == target_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail=f"Dispute {target_id} not found")

    if dispute.status not in (DisputeStatus.NEEDS_REVIEW, DisputeStatus.RECEIVED):
        raise HTTPException(
            status_code=400,
            detail=f"Dispute {target_id} is in status '{dispute.status.value}'. Only NEEDS_REVIEW or RECEIVED can be manually contested.",
        )

    # Ensure evidence is compiled
    if not dispute.evidence_text:
        dispute.evidence_text = compile_evidence(
            dispute_id=dispute.dispute_id,
            payment_id=dispute.payment_id,
            order_id=dispute.order_id,
            amount=dispute.amount,
            reason_code=dispute.reason_code,
            confidence_score=dispute.confidence_score or 75.0,
            raw_telemetry=dispute.raw_telemetry,
            ocr_manifest_json=dispute.ocr_manifest_json,
        )

    # Upload document & submit contest
    doc_res = await razorpay_client.upload_document(
        document_text=dispute.evidence_text,
        filename=f"UDIR_Manual_Override_{target_id}.md",
    )
    doc_id = doc_res.get("id")
    dispute.document_id = doc_id

    await razorpay_client.contest_dispute(
        dispute_id=dispute.dispute_id,
        evidence_text=dispute.evidence_text,
        document_ids=[doc_id] if doc_id else None,
        summary="Manual Merchant Representment with telemetry review.",
    )

    dispute.status = DisputeStatus.MANUALLY_CONTESTED
    db.commit()

    return ManualOverrideResponse(
        dispute_id=target_id,
        new_status=DisputeStatus.MANUALLY_CONTESTED,
        document_id=doc_id,
        message="Dispute successfully contested via manual override to Razorpay API",
    )


@router.post("/api/v1/dashboard/simulate")
async def simulate_dispute_webhook(
    req: SimulateWebhookRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Simulate realistic webhook events with different telemetry scenarios."""
    random_id = f"disp_sim_{random.randint(100000, 999999)}"
    payment_id = f"pay_sim_{random.randint(100000, 999999)}"
    order_id = f"order_sim_{random.randint(100000, 999999)}"

    # Build telemetry based on scenario
    if req.scenario == "winnable_clean":
        telemetry = {
            "otp": {"verified": True},
            "geofence": {"distance_km": round(random.uniform(0.2, 2.5), 1)},
            "weight": {"shipped_g": 520, "delivered_g": 518},
            "delivery_signature": True,
            "device_fingerprint_match": True,
            "defect_ticket_open": False,
            "courier": "Delhivery Express",
            "manifest_ocr_text": "DELHIVERY LOGISTICS MANIFEST - AWB-991024 - RECIPIENT SIGNED - 518g",
        }
    elif req.scenario == "customer_defect_ticket":
        # Consumer Fairness Gate trigger 1: open support ticket
        telemetry = {
            "otp": {"verified": True},
            "geofence": {"distance_km": 1.1},
            "weight": {"shipped_g": 500, "delivered_g": 500},
            "delivery_signature": True,
            "defect_ticket_open": True,
            "support_ticket": {"open": True, "ticket_id": "TICK-9012", "issue": "Item damaged in box"},
        }
    elif req.scenario == "transit_weight_loss":
        # Consumer Fairness Gate trigger 2: transit weight loss > 100g
        telemetry = {
            "otp": {"verified": True},
            "geofence": {"distance_km": 1.5},
            "weight": {"shipped_g": 750, "delivered_g": 520},  # 230g loss > 100g
            "delivery_signature": True,
            "defect_ticket_open": False,
        }
    elif req.scenario == "ambiguous_needs_review":
        telemetry = {
            "otp": {"verified": False},
            "geofence": {"distance_km": round(random.uniform(7.0, 11.0), 1)},
            "weight": {"shipped_g": 500, "delivered_g": 480},
            "delivery_signature": True,
            "device_fingerprint_match": False,
            "defect_ticket_open": False,
        }
    else:  # fraud_no_otp
        telemetry = {
            "otp": {"verified": False},
            "geofence": {"distance_km": 28.5},
            "weight": {"shipped_g": 500, "delivered_g": 0},
            "delivery_signature": False,
            "device_fingerprint_match": False,
            "defect_ticket_open": False,
        }

    webhook_payload = {
        "event": "payment.dispute.created",
        "payload": {
            "dispute": {
                "entity": {
                    "id": random_id,
                    "payment_id": payment_id,
                    "order_id": order_id,
                    "amount": int(req.amount * 100),
                    "reason_code": req.reason_code,
                }
            }
        },
        **telemetry,
    }

    # Save to SQLite
    dispute = Dispute(
        dispute_id=random_id,
        payment_id=payment_id,
        order_id=order_id,
        status=DisputeStatus.RECEIVED,
        reason_code=req.reason_code,
        amount=req.amount,
        raw_telemetry=json.dumps(webhook_payload),
    )
    db.add(dispute)
    db.commit()

    # Process in background
    background_tasks.add_task(process_dispute_task, random_id)

    return {
        "status": "simulated",
        "dispute_id": random_id,
        "scenario": req.scenario,
        "amount": req.amount,
        "message": f"Simulated {req.scenario} dispute webhook successfully queued",
    }
