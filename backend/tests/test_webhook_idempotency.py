"""Unit tests verifying webhook idempotency and atomic AuditJob creation."""

import hashlib
import hmac
import json

from app.core.models import AuditJob, Dispute

SECRET = "test_webhook_secret_key_123"


def compute_sig(body: bytes, secret: str = SECRET) -> str:
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def test_webhook_idempotency_duplicate_event(client, db_session):
    """Assert submitting the same event twice results in single DB row and duplicate response."""
    payload = {
        "dispute_id": "disp_idemp_9999",
        "payment_id": "pay_idemp_9999",
        "amount": 4999.0,
        "reason_code": "product_not_received",
    }
    raw = json.dumps(payload).encode("utf-8")
    sig = compute_sig(raw)
    headers = {
        "Content-Type": "application/json",
        "X-Razorpay-Signature": sig,
        "X-Razorpay-Event-Id": "event_fixed_idempotent_key_1",
    }

    # First ingestion -> inserted
    res1 = client.post("/api/webhook", content=raw, headers=headers)
    assert res1.status_code == 200
    assert res1.json()["decision"] == "inserted"

    # Second ingestion -> duplicate
    res2 = client.post("/api/webhook", content=raw, headers=headers)
    assert res2.status_code == 200
    assert res2.json()["decision"] == "duplicate"

    # Verify only single dispute and single audit job in database
    dispute_count = (
        db_session.query(Dispute).filter(Dispute.razorpay_dispute_id == "disp_idemp_9999").count()
    )
    job_count = db_session.query(AuditJob).filter(AuditJob.dispute_id == "disp_idemp_9999").count()

    assert dispute_count == 1
    assert job_count == 1
