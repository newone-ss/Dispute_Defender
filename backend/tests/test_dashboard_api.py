"""Integration tests for Dashboard REST endpoints and admin override security."""

from app.core.models import Dispute, DisputeStatus


def test_healthz_endpoint(client):
    """Verify /healthz returns 200 with component reachability."""
    res = client.get("/healthz")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "database" in data
    assert "chromadb" in data


def test_metrics_and_disputes_list(client, db_session):
    """Verify metrics calculation and paginated list returns."""
    d1 = Dispute(
        razorpay_dispute_id="disp_m1",
        idempotency_key="k1",
        reason_code="product_not_received",
        amount_paise=200000,
        status=DisputeStatus.AUTO_CONTESTED,
    )
    d2 = Dispute(
        razorpay_dispute_id="disp_m2",
        idempotency_key="k2",
        reason_code="defective_merchandise",
        amount_paise=150000,
        status=DisputeStatus.AUTO_ACCEPTED,
    )
    db_session.add_all([d1, d2])
    db_session.commit()

    res = client.get("/api/metrics")
    assert res.status_code == 200
    m = res.json()
    assert m["total_disputes"] == 2
    assert m["auto_contested_count"] == 1
    assert m["auto_accepted_count"] == 1
    assert m["net_inr_saved"] == 2000.0
    assert m["bank_penalties_avoided"] == 1500.0

    res_list = client.get("/api/disputes")
    assert res_list.status_code == 200
    assert res_list.json()["total"] == 2


def test_manual_override_security(client, db_session):
    """Verify manual override requires valid X-Admin-Token header."""
    d = Dispute(
        razorpay_dispute_id="disp_ov1",
        idempotency_key="kov1",
        reason_code="product_not_received",
        amount_paise=250000,
        status=DisputeStatus.NEEDS_REVIEW,
    )
    db_session.add(d)
    db_session.commit()

    override_payload = {"action": "contest", "operator_note": "Verified customer signed POD"}

    # Unauthorized without token
    res_unauth = client.post("/api/disputes/disp_ov1/override", json=override_payload)
    assert res_unauth.status_code == 401

    # Unauthorized with bad token
    res_bad = client.post(
        "/api/disputes/disp_ov1/override",
        json=override_payload,
        headers={"X-Admin-Token": "wrong_token_123"},
    )
    assert res_bad.status_code == 401

    # Authorized with valid token
    res_ok = client.post(
        "/api/disputes/disp_ov1/override",
        json=override_payload,
        headers={"X-Admin-Token": "test_admin_token_xyz"},
    )
    assert res_ok.status_code == 200
    assert res_ok.json()["new_status"] == DisputeStatus.MANUALLY_CONTESTED.value


def test_simulate_endpoint(client):
    """Verify simulation endpoint inserts dispute and queues audit job."""
    res = client.post(
        "/api/simulate",
        json={
            "scenario": "winnable_clean",
            "amount_inr": 2499.0,
            "reason_code": "product_not_received",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == DisputeStatus.RECEIVED.value
    assert data["amount_inr"] == 2499.0
