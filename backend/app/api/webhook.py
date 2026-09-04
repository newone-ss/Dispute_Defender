"""Critical-path webhook ingestion endpoint with HMAC verification and idempotency."""

import hashlib
import hmac
import json
import logging
import time
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_config
from app.core.database import get_db
from app.core.models import AuditJob, Dispute, DisputeStatus, JobStatus
from app.core.schemas import WebhookResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["webhooks"])
config = get_config()


def verify_signature(raw_body: bytes, signature_header: Optional[str]) -> bool:
    """Verify incoming X-Razorpay-Signature using constant-time HMAC-SHA256 comparison."""
    if not signature_header:
        return False

    # Optional testing bypass only in mock development
    if config.app_env == "development" and signature_header == "mock_signature_dev":
        return True

    expected = hmac.new(
        config.razorpay_webhook_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, signature_header)


@router.post(
    "/webhook",
    response_model=WebhookResponse,
    status_code=status.HTTP_200_OK,
    summary="Ingest Razorpay chargeback webhooks in sub-25ms with HMAC verification",
)
async def ingest_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_razorpay_signature: Optional[str] = Header(None, alias="X-Razorpay-Signature"),
    x_razorpay_event_id: Optional[str] = Header(None, alias="X-Razorpay-Event-Id"),
) -> WebhookResponse:
    """Ingest Razorpay dispute events with atomic idempotency and durable queueing."""
    start_time = time.perf_counter()
    raw_body = await request.body()

    # 1. HMAC Signature Verification
    if not verify_signature(raw_body, x_razorpay_signature):
        logger.warning(
            "Webhook signature verification failed",
            extra={"event": "webhook_unauthorized", "latency_ms": 0.0},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Razorpay-Signature header",
        )

    # 2. Parse payload safely
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload")

    # 3. Extract dispute attributes
    dispute_entity = payload.get("payload", {}).get("dispute", {}).get("entity", {})
    dispute_id = dispute_entity.get("id") or payload.get("dispute_id")
    if not dispute_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing dispute identifier in payload"
        )

    payment_id = dispute_entity.get("payment_id") or payload.get("payment_id")
    reason_code = dispute_entity.get("reason_code") or payload.get("reason_code") or "general"
    created_at_raw = (
        dispute_entity.get("created_at") or payload.get("created_at") or int(time.time())
    )

    amount_paise = dispute_entity.get("amount")
    if amount_paise is None:
        amount_paise = int(float(payload.get("amount", 2499.0)) * 100)

    # 4. Deterministic idempotency key
    idempotency_key = x_razorpay_event_id or f"{dispute_id}:{created_at_raw}"

    # 5. Atomic persist: Dispute + AuditJob within single transaction
    decision = "inserted"
    try:
        dispute = Dispute(
            razorpay_dispute_id=dispute_id,
            payment_id=payment_id,
            idempotency_key=idempotency_key,
            reason_code=reason_code,
            amount_paise=amount_paise,
            currency="INR",
            status=DisputeStatus.RECEIVED,
            telemetry=payload,
            audit_log=[
                {
                    "from_status": None,
                    "to_status": DisputeStatus.RECEIVED.value,
                    "timestamp": time.time(),
                    "reason": "Webhook ingested",
                }
            ],
        )
        db.add(dispute)

        audit_job = AuditJob(
            dispute_id=dispute_id,
            status=JobStatus.PENDING,
        )
        db.add(audit_job)
        db.commit()

    except IntegrityError:
        # Idempotency hit: already processed this key or duplicate dispute
        db.rollback()
        decision = "duplicate"

    latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
    logger.info(
        f"Webhook handled: dispute={dispute_id} decision={decision} latency={latency_ms}ms",
        extra={
            "dispute_id": dispute_id,
            "event": "webhook_ingest",
            "decision": decision,
            "latency_ms": latency_ms,
        },
    )

    return WebhookResponse(
        status="received",
        dispute_id=dispute_id,
        decision=decision,
        latency_ms=latency_ms,
    )
