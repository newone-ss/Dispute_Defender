"""Durable Audit Queue Worker daemon.

Production Hardening & Cloud Migration Roadmap:
To migrate this worker from local SQLite to Celery, Arq, or AWS SQS, wrap the `process_dispute`
function in a task handler (e.g., `@celery_app.task(bind=True, max_retries=3)` or SQS message consumer).
The core business logic (manifest parsing, pure scoring, fairness gate, evidence compilation,
and Razorpay client calls) remains 100% unchanged.
"""

import argparse
import logging
import time
from typing import Optional

from sqlalchemy.orm import Session

from app.config import get_config
from app.core.compiler import compile_packet
from app.core.database import SessionLocal
from app.core.models import Dispute, DisputeStatus
from app.core.ocr_extractor import parse_manifest
from app.core.policy_rag import retrieve_policy_clauses
from app.core.queue import claim_job, complete_job, fail_or_retry_job
from app.core.rag_engine import search_support_tickets
from app.core.razorpay_client import RazorpayClientError, razorpay_client
from app.core.schemas import TelemetryData
from app.logging_config import configure_logging
from app.policy.fairness_gate import fairness_gate, load_scoring_policy, resolve_decision
from app.policy.reason_codes import ReasonCodeRegistry
from app.policy.scoring_engine import score

logger = logging.getLogger("audit_worker")
config = get_config()


def _extract_telemetry_model(raw_telemetry: Optional[dict]) -> TelemetryData:
    """Normalize raw telemetry dictionary into typed TelemetryData model."""
    raw = raw_telemetry or {}
    wt = raw.get("weight", {})
    geo = raw.get("geofence", {})
    otp = raw.get("otp", {})
    pod = raw.get("pod", {})
    dev = raw.get("device", {})

    return TelemetryData(
        delivery_type=str(raw.get("delivery_type", "STANDARD")).upper(),
        otp_verified=bool(
            otp.get("verified") if isinstance(otp, dict) else raw.get("otp_verified")
        ),
        geofence_distance_m=(
            float(geo.get("distance_m"))
            if isinstance(geo, dict) and geo.get("distance_m") is not None
            else None
        ),
        geofence_distance_km=(
            float(geo.get("distance_km"))
            if isinstance(geo, dict) and geo.get("distance_km") is not None
            else float(raw.get("geofence_distance_km"))
            if raw.get("geofence_distance_km") is not None
            else None
        ),
        shipped_weight_g=(
            float(wt.get("shipped_g"))
            if isinstance(wt, dict) and wt.get("shipped_g") is not None
            else float(raw.get("shipped_weight_g"))
            if raw.get("shipped_weight_g") is not None
            else None
        ),
        delivered_weight_g=(
            float(wt.get("delivered_g"))
            if isinstance(wt, dict) and wt.get("delivered_g") is not None
            else float(raw.get("delivered_weight_g"))
            if raw.get("delivered_weight_g") is not None
            else None
        ),
        delivery_signature=bool(
            pod.get("exists") if isinstance(pod, dict) else raw.get("delivery_signature", False)
        ),
        device_fingerprint_match=bool(
            dev.get("fingerprint_match")
            if isinstance(dev, dict)
            else raw.get("device_fingerprint_match", False)
        ),
        defect_ticket_open=bool(
            raw.get("defect_ticket_open") or raw.get("support_ticket", {}).get("open")
        ),
        raw_ocr_text=raw.get("manifest_ocr_text") or raw.get("raw_ocr_text"),
        courier=raw.get("courier"),
        awb_number=raw.get("awb_number"),
    )


def process_dispute(dispute_id: str, db: Session) -> None:
    """Execute the full 8-step idempotent audit and representment pipeline."""
    dispute = db.query(Dispute).filter(Dispute.razorpay_dispute_id == dispute_id).first()
    if not dispute:
        logger.error(
            f"Dispute {dispute_id} not found in database", extra={"dispute_id": dispute_id}
        )
        return

    # Check terminal state idempotency
    terminal_states = {
        DisputeStatus.AUTO_CONTESTED,
        DisputeStatus.AUTO_ACCEPTED,
        DisputeStatus.MANUALLY_CONTESTED,
        DisputeStatus.MANUALLY_ACCEPTED,
        DisputeStatus.WON,
        DisputeStatus.LOST,
    }
    if dispute.status in terminal_states:
        logger.warning(
            f"Dispute {dispute_id} already in terminal state {dispute.status.value}. Skipping re-audit.",
            extra={"dispute_id": dispute_id, "event": "skip_terminal_state"},
        )
        return

    dispute.status = DisputeStatus.PROCESSING
    db.commit()

    # Step 1: Parse telemetry & manifest OCR if text present
    telemetry = _extract_telemetry_model(dispute.telemetry)
    if telemetry.raw_ocr_text:
        manifest = parse_manifest(telemetry.raw_ocr_text)
        if manifest.courier_partner:
            telemetry.courier = manifest.courier_partner
        if manifest.awb_number:
            telemetry.awb_number = manifest.awb_number
        if manifest.signature_present:
            telemetry.delivery_signature = True

    # Step 2: Pure scoring and reason code lookup
    policy = load_scoring_policy(config.scoring_policy_path)
    score_breakdown = score(telemetry, policy)
    reason_entry, is_unmapped = ReasonCodeRegistry.normalize(dispute.reason_code)

    # Step 3 & 4: RAG support ticket search & policy retrieval
    support_hits = search_support_tickets(dispute_id)
    citations = retrieve_policy_clauses(reason_entry.code)

    # Step 5: Pure Fairness Gate & Master Decision
    gate = fairness_gate(telemetry, support_hits, policy)
    decision, decision_reason = resolve_decision(
        score_breakdown=score_breakdown,
        gate_result=gate,
        reason_entry=reason_entry,
        delivery_type=telemetry.delivery_type,
        is_unmapped=is_unmapped,
        policy=policy,
    )

    # Step 6: Evidence compilation if contesting
    packet_text = None
    if decision == DisputeStatus.AUTO_CONTESTED:
        packet_text = compile_packet(
            dispute_id=dispute.razorpay_dispute_id,
            payment_id=dispute.payment_id,
            amount_inr=float(dispute.amount_paise) / 100.0,
            reason_code=reason_entry.code,
            score=score_breakdown.total_score,
            telemetry=telemetry,
            citations=citations,
            fairness=gate,
        )

    # Step 7: Call Razorpay APIs
    doc_id = None
    if decision == DisputeStatus.AUTO_CONTESTED and packet_text:
        doc_ref = razorpay_client.upload_evidence(packet_text, f"UDIR_{dispute_id}.md")
        doc_id = doc_ref.id
        razorpay_client.contest(dispute_id, document_id=doc_id, summary=decision_reason)
    elif decision == DisputeStatus.AUTO_ACCEPTED:
        razorpay_client.accept(dispute_id)

    # Step 8: Update Dispute record and append transition to audit log
    dispute.status = decision
    dispute.score = score_breakdown.total_score
    dispute.decision_reason = decision_reason
    dispute.evidence_packet = packet_text

    current_log = list(dispute.audit_log or [])
    current_log.append(
        {
            "from_status": DisputeStatus.PROCESSING.value,
            "to_status": decision.value,
            "timestamp": time.time(),
            "score": score_breakdown.total_score,
            "reason": decision_reason,
            "document_id": doc_id,
            "policy_version": policy.get("policy_version", "2026.1.0"),
        }
    )
    dispute.audit_log = current_log
    db.commit()

    logger.info(
        f"Audit completed: dispute={dispute_id} score={score_breakdown.total_score} decision={decision.value}",
        extra={
            "dispute_id": dispute_id,
            "event": "audit_decision",
            "decision": decision.value,
            "policy_version": policy.get("policy_version"),
        },
    )


def run_worker_loop(once: bool = False) -> None:
    """Run worker daemon polling the durable queue."""
    configure_logging(config.log_level)
    policy = load_scoring_policy(config.scoring_policy_path)
    logger.info(
        f"Starting Dispute Defender Audit Worker (policy_version={policy.get('policy_version')})",
        extra={"event": "worker_start", "policy_version": policy.get("policy_version")},
    )

    while True:
        db = SessionLocal()
        try:
            job = claim_job(db, lease_seconds=config.audit_job_lease_seconds)
            if job:
                dispute_id = job.dispute_id
                logger.info(f"Claimed audit job #{job.id} for dispute {dispute_id}")
                try:
                    process_dispute(dispute_id, db)
                    complete_job(db, job.id)
                except RazorpayClientError as rzp_err:
                    logger.error(f"Razorpay API error on dispute {dispute_id}: {rzp_err}")
                    fail_or_retry_job(db, job.id, f"Razorpay API Error: {rzp_err}")
                except Exception as ex:
                    logger.exception(f"Unexpected error processing dispute {dispute_id}: {ex}")
                    fail_or_retry_job(db, job.id, str(ex))
            else:
                if once:
                    break
                time.sleep(config.audit_worker_poll_interval_seconds)
        finally:
            db.close()

        if once:
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dispute Defender Audit Queue Worker")
    parser.add_argument("--once", action="store_true", help="Process at most one job and exit")
    args = parser.parse_args()
    run_worker_loop(once=args.once)
