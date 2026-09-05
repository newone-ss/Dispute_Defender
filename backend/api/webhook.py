"""Razorpay chargeback webhook ingestion router with FastAPI BackgroundTasks."""

import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

from core.database import SessionLocal
from core.mock_razorpay import rzp_client
from data.models import Dispute, Telemetry

logger = logging.getLogger("webhook")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

router = APIRouter(tags=["webhooks"])


# ---------------------------------------------------------------------------
# Pydantic Schemas for Razorpay Webhook Payload
# ---------------------------------------------------------------------------


class DisputeEntity(BaseModel):
    """Inner dispute entity provided by Razorpay webhook."""

    id: Optional[str] = None
    payment_id: Optional[str] = None
    reason_code: Optional[str] = None
    amount: Optional[int] = None


class DisputePayload(BaseModel):
    """Container wrapping the dispute entity."""

    entity: Optional[DisputeEntity] = None


class WebhookPayloadContainer(BaseModel):
    """Outer container for Razorpay event payloads."""

    dispute: Optional[DisputePayload] = None


class RazorpayWebhookPayload(BaseModel):
    """Full Razorpay Webhook event payload supporting nested & flat structures."""

    event: Optional[str] = "payment.dispute.created"
    payload: Optional[WebhookPayloadContainer] = None

    # Optional flat fields for direct API testing or simulation
    dispute_id: Optional[str] = None
    payment_id: Optional[str] = None
    reason_code: Optional[str] = None
    amount: Optional[int] = None

    def extract_dispute_data(self) -> tuple[str, str, str, int]:
        """Safely extract (dispute_id, payment_id, reason_code, amount)."""
        if self.payload and self.payload.dispute and self.payload.dispute.entity:
            entity = self.payload.dispute.entity
            d_id = entity.id or self.dispute_id or "disp_mock"
            p_id = entity.payment_id or self.payment_id or "pay_mock"
            r_code = entity.reason_code or self.reason_code or "fraud"
            amt = entity.amount if entity.amount is not None else (self.amount or 0)
            return d_id, p_id, r_code, amt

        return (
            self.dispute_id or "disp_mock",
            self.payment_id or "pay_mock",
            self.reason_code or "fraud",
            self.amount or 0,
        )


# ---------------------------------------------------------------------------
# Background Task AI Logic
# ---------------------------------------------------------------------------


def process_dispute_background(
    dispute_id: str,
    payment_id: str,
    reason_code: str,
    amount: int,
) -> None:
    """Asynchronous background worker executing courier telemetry checks and contestation."""
    db = SessionLocal()
    try:
        logger.info(
            f"[BackgroundTask] Processing dispute: dispute_id='{dispute_id}', "
            f"payment_id='{payment_id}', amount={amount}"
        )

        # 1. Query Telemetry for the given payment_id
        telemetry = db.query(Telemetry).filter(Telemetry.payment_id == payment_id).first()

        # 2. Retrieve or create the Dispute record in SQLite
        dispute = db.query(Dispute).filter(Dispute.dispute_id == dispute_id).first()
        if not dispute:
            dispute = Dispute(
                dispute_id=dispute_id,
                payment_id=payment_id,
                reason_code=reason_code,
                amount=amount,
                status="under_review",
            )
            db.add(dispute)
            db.flush()

        # 3. Simulate AI Resolution Logic:
        # If telemetry exists and otp_verified is True -> Upload evidence and contest dispute
        if telemetry and telemetry.otp_verified:
            logger.info(
                f"[AI Resolution] Doorstep OTP verified for payment '{payment_id}'. "
                f"Contesting dispute '{dispute_id}' with mock proof."
            )
            doc_id = rzp_client.upload_evidence_document("evidence/proof_of_delivery.pdf")
            rzp_client.contest_dispute(dispute_id=dispute_id, document_id=doc_id)
            dispute.status = "contested"
        else:
            logger.info(
                f"[AI Resolution] Telemetry missing or unverified for payment '{payment_id}'. "
                f"Dispute '{dispute_id}' marked as 'needs_review'."
            )
            dispute.status = "needs_review"

        db.commit()
        logger.info(
            f"[BackgroundTask] Completed for dispute '{dispute_id}'. Final status: '{dispute.status}'"
        )
    except Exception as exc:
        db.rollback()
        logger.error(
            f"[BackgroundTask] Failed to process dispute '{dispute_id}': {exc}", exc_info=True
        )
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Webhook Ingestion Route
# ---------------------------------------------------------------------------


@router.post("/webhook/razorpay")
async def razorpay_webhook(
    payload: RazorpayWebhookPayload,
    background_tasks: BackgroundTasks,
):
    """Ingest Razorpay webhook, offload resolution to BackgroundTasks, and respond instantly."""
    dispute_id, payment_id, reason_code, amount = payload.extract_dispute_data()

    # Offload resolution logic to BackgroundTasks
    background_tasks.add_task(
        process_dispute_background,
        dispute_id=dispute_id,
        payment_id=payment_id,
        reason_code=reason_code,
        amount=amount,
    )

    # Return immediately to avoid timeout disconnects from Razorpay's webhook delivery system
    return {"status": "ok", "message": "Webhook received"}
