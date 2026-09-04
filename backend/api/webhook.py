"""Webhook Router & Asynchronous Dispute Processing Pipeline.

CRITICAL DESIGN:
- Returns 200 OK immediately to acknowledge receipt from Razorpay.
- Schedules end-to-end audit and representment generation via FastAPI BackgroundTasks.
- Hybrid Gate: RAG omnichannel fairness → Deterministic telemetry → Consumer Fairness Gate.
- Reason-Code Routing: OBD defective merchandise auto-contest, standard defective → NEEDS_REVIEW.
- High confidence (>80) → uploads NPCI UDIR packet to Documents API and calls Contest API.
"""

import json
import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, BackgroundTasks, Request, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.database import SessionLocal
from core.models import Dispute, DisputeStatus
from core.audit_engine import evaluate_telemetry
from core.compiler import compile_evidence
from core.ocr_extractor import parse_manifest_text_deterministic
from core.razorpay_client import razorpay_client
from core.rag_engine import evaluate_rag_fairness_sync
from core.policy_rag import get_policy_checklist

logger = logging.getLogger(__name__)
router = APIRouter(tags=["webhooks"])


def process_dispute_task(dispute_id: str) -> None:
    """Asynchronous background worker executing the hybrid audit & contest pipeline."""
    db: Session = SessionLocal()
    try:
        dispute = db.query(Dispute).filter(Dispute.dispute_id == dispute_id).first()
        if not dispute:
            logger.error(f"Background task: Dispute {dispute_id} not found in database")
            return

        dispute.status = DisputeStatus.PROCESSING
        db.commit()

        # ── 1. Parse Manifest OCR if present in telemetry ────────────────────
        raw_dict = {}
        if dispute.raw_telemetry:
            try:
                raw_dict = json.loads(dispute.raw_telemetry)
            except Exception:
                pass

        ocr_manifest_json = dispute.ocr_manifest_json
        if not ocr_manifest_json:
            manifest_text = raw_dict.get("manifest_ocr_text") or raw_dict.get("raw_ocr_text")
            if manifest_text:
                extracted = parse_manifest_text_deterministic(manifest_text)
                ocr_manifest_json = extracted.model_dump_json()
                dispute.ocr_manifest_json = ocr_manifest_json

        # ── 2. Extract delivery type ────────────────────────────────────────
        delivery_type = (
            raw_dict.get("delivery_type")
            or dispute.delivery_type
            or "STANDARD"
        ).upper()
        dispute.delivery_type = delivery_type

        # ── 3. RAG Omnichannel Fairness Gate ────────────────────────────────
        rag_result = evaluate_rag_fairness_sync(
            dispute_id=dispute.dispute_id,
            order_id=dispute.order_id or "",
        )
        dispute.rag_fairness_triggered = rag_result.triggered
        dispute.rag_fairness_summary = rag_result.summary

        # ── 4. Policy RAG — Fetch evidence checklist ────────────────────────
        reason_code = dispute.reason_code or raw_dict.get("reason_code", "product_not_received")
        policy = get_policy_checklist(
            reason_code=reason_code,
            delivery_type=delivery_type,
            use_rag=True,
        )
        policy_json = policy.model_dump_json()
        dispute.policy_checklist_json = policy_json

        # ── 5. Run Deterministic Audit with Hybrid Gates ────────────────────
        audit = evaluate_telemetry(
            raw_telemetry=dispute.raw_telemetry,
            delivery_type=delivery_type,
            reason_code=reason_code,
            rag_fairness_triggered=rag_result.triggered,
            rag_fairness_summary=rag_result.summary,
            policy_checklist_json=policy_json,
        )

        dispute.confidence_score = audit.confidence_score
        dispute.otp_verified = audit.otp_verified
        dispute.geofence_distance_km = audit.geofence_distance_km
        dispute.geofence_distance_m = audit.geofence_distance_m
        dispute.shipped_weight_g = audit.shipped_weight_g
        dispute.delivered_weight_g = audit.delivered_weight_g
        dispute.weight_loss_g = audit.weight_loss_g
        dispute.defect_ticket_open = (
            raw_dict.get("defect_ticket_open") is True
            or raw_dict.get("support_ticket", {}).get("open") is True
        )
        dispute.fairness_gate_triggered = audit.fairness_gate_triggered
        dispute.fairness_reason = audit.fairness_reason
        dispute.status = audit.decision

        logger.info(
            f"Dispute {dispute_id}: Score={audit.confidence_score}, "
            f"Decision={audit.decision.value}, DeliveryType={delivery_type}, "
            f"Route={audit.reason_code_route}, "
            f"FairnessGate={audit.fairness_gate_triggered}, "
            f"RAGFairness={rag_result.triggered}"
        )

        # ── 6. Compile NPCI UDIR Representment Packet ────────────────────────
        evidence_text = compile_evidence(
            dispute_id=dispute.dispute_id,
            payment_id=dispute.payment_id,
            order_id=dispute.order_id,
            amount=dispute.amount,
            reason_code=dispute.reason_code,
            confidence_score=audit.confidence_score,
            raw_telemetry=dispute.raw_telemetry,
            ocr_manifest_json=dispute.ocr_manifest_json,
            delivery_type=delivery_type,
            rag_fairness_summary=rag_result.summary if rag_result.triggered else None,
            policy_checklist_json=policy_json,
            geofence_distance_m=audit.geofence_distance_m,
        )
        dispute.evidence_text = evidence_text

        # ── 7. Execute API Actions (Contest vs Accept) ───────────────────────
        if audit.decision == DisputeStatus.AUTO_CONTESTED:
            logger.info(f"Uploading NPCI UDIR evidence document for dispute {dispute_id}...")
            doc_res = razorpay_client.upload_document_sync(
                document_text=evidence_text,
                filename=f"UDIR_Evidence_{dispute_id}.md",
                purpose="dispute_evidence",
            )
            doc_id = doc_res.get("id")
            dispute.document_id = doc_id

            logger.info(f"Submitting contest via Razorpay API for dispute {dispute_id}...")
            razorpay_client.contest_dispute_sync(
                dispute_id=dispute.dispute_id,
                evidence_text=evidence_text,
                document_ids=[doc_id] if doc_id else None,
            )

        elif audit.decision == DisputeStatus.AUTO_ACCEPTED:
            logger.info(f"Accepting dispute {dispute_id} via Razorpay API (Liability released)...")
            razorpay_client.accept_dispute_sync(dispute.dispute_id)

        elif audit.decision == DisputeStatus.NEEDS_REVIEW:
            logger.info(f"Dispute {dispute_id} placed in NEEDS_REVIEW queue for merchant review")

        db.commit()

    except Exception as e:
        logger.exception(f"Error processing dispute {dispute_id}: {e}")
        db.rollback()
        try:
            dispute = db.query(Dispute).filter(Dispute.dispute_id == dispute_id).first()
            if dispute:
                dispute.status = DisputeStatus.NEEDS_REVIEW
                db.commit()
        except Exception:
            db.rollback()
    finally:
        db.close()


@router.post("/webhook", status_code=200)
@router.post("/api/v1/webhook", status_code=200)
async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
    """Non-blocking Webhook Ingestion endpoint.

    Flow:
    1. Parse JSON payload immediately.
    2. Extract dispute ID, payment ID, amount, order ID, and delivery_type.
    3. Persist record to SQLite in RECEIVED status with raw JSON telemetry.
    4. Queue process_dispute_task in BackgroundTasks.
    5. Return 200 OK immediately.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    # Extract dispute entities from Razorpay standard structure
    event_type = body.get("event", "payment.dispute.created")
    payload = body.get("payload", {})
    dispute_entity = payload.get("dispute", {}).get("entity", {})

    dispute_id = dispute_entity.get("id") or body.get("dispute_id")
    if not dispute_id:
        logger.warning("Webhook received without dispute_id")
        return {"status": "ignored", "reason": "Missing dispute_id in payload"}

    payment_id = dispute_entity.get("payment_id") or body.get("payment_id")
    order_id = dispute_entity.get("order_id") or body.get("order_id")
    reason_code = dispute_entity.get("reason_code") or body.get("reason_code") or "product_not_received"
    delivery_type = dispute_entity.get("delivery_type") or body.get("delivery_type") or "STANDARD"

    amount_paise = dispute_entity.get("amount")
    if amount_paise is not None:
        amount_inr = float(amount_paise) / 100.0
    else:
        amount_inr = float(body.get("amount", 2499.0))

    # Persist to SQLite
    db = SessionLocal()
    try:
        existing = db.query(Dispute).filter(Dispute.dispute_id == dispute_id).first()
        if not existing:
            dispute = Dispute(
                dispute_id=dispute_id,
                payment_id=payment_id,
                order_id=order_id,
                status=DisputeStatus.RECEIVED,
                reason_code=reason_code,
                amount=amount_inr,
                delivery_type=delivery_type.upper(),
                raw_telemetry=json.dumps(body),
            )
            db.add(dispute)
            db.commit()
            logger.info(f"Ingested webhook dispute {dispute_id} -> SQLite (delivery_type={delivery_type})")
        else:
            logger.info(f"Dispute {dispute_id} already exists, updating raw telemetry")
            existing.raw_telemetry = json.dumps(body)
            existing.delivery_type = delivery_type.upper()
            db.commit()
    except IntegrityError:
        db.rollback()
    except Exception as e:
        db.rollback()
        logger.error(f"Database error on webhook ingestion: {e}")
        raise HTTPException(status_code=500, detail="Database write error")
    finally:
        db.close()

    # Queue background verification pipeline
    background_tasks.add_task(process_dispute_task, dispute_id)

    return {
        "status": "received",
        "dispute_id": dispute_id,
        "delivery_type": delivery_type,
        "message": "Dispute verification pipeline queued asynchronously (Hybrid RAG + Deterministic)",
    }
