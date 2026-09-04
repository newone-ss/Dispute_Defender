"""Unit tests verifying HMAC-SHA256 signature enforcement on webhooks."""

import hashlib
import hmac
import json

SECRET = "test_webhook_secret_key_123"


def compute_sig(body: bytes, secret: str = SECRET) -> str:
    """Compute valid HMAC-SHA256 signature."""
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def test_missing_signature_rejected_with_401(client):
    """Assert requests lacking X-Razorpay-Signature header are rejected."""
    payload = {"dispute_id": "disp_test_sig_01", "amount": 1999.0}
    res = client.post("/api/webhook", json=payload)
    assert res.status_code == 401
    assert "Invalid or missing" in res.json()["detail"]


def test_invalid_signature_rejected_with_401(client):
    """Assert requests with tampered signatures are rejected."""
    payload = {"dispute_id": "disp_test_sig_02", "amount": 1999.0}
    raw = json.dumps(payload).encode("utf-8")
    res = client.post(
        "/api/webhook",
        content=raw,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": "tampered_fake_signature_hash_xyz",
        },
    )
    assert res.status_code == 401


def test_valid_signature_accepted_with_200(client):
    """Assert requests with authentic HMAC signatures return 200."""
    payload = {"dispute_id": "disp_test_sig_03", "amount": 1999.0}
    raw = json.dumps(payload).encode("utf-8")
    sig = compute_sig(raw)
    res = client.post(
        "/api/webhook",
        content=raw,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": sig},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "received"
    assert data["decision"] == "inserted"
    assert data["dispute_id"] == "disp_test_sig_03"
