"""Unit tests verifying Consumer Fairness Gate pure logic."""

from app.config import get_config
from app.core.models import DisputeStatus
from app.core.schemas import ChatHit, TelemetryData
from app.policy.fairness_gate import fairness_gate, load_scoring_policy, resolve_decision
from app.policy.reason_codes import ReasonCodeRegistry
from app.policy.scoring_engine import score

config = get_config()
policy = load_scoring_policy(config.scoring_policy_path)


def test_transit_weight_loss_triggers_fairness_gate():
    """Assert transit weight loss > 100g immediately triggers AUTO_ACCEPT."""
    # Dispatched 850g, delivered 510g (340g loss)
    telemetry = TelemetryData(
        otp_verified=True,
        geofence_distance_m=35.0,
        shipped_weight_g=850.0,
        delivered_weight_g=510.0,
        delivery_signature=True,
    )
    gate = fairness_gate(telemetry, support_tickets=[], policy=policy)
    assert gate.triggered is True
    assert gate.action == "AUTO_ACCEPT"
    assert "Transit weight loss of 340.0g" in gate.reason

    score_res = score(telemetry, policy)
    reason_entry, _ = ReasonCodeRegistry.normalize("product_not_received")
    decision, dec_reason = resolve_decision(
        score_breakdown=score_res,
        gate_result=gate,
        reason_entry=reason_entry,
        policy=policy,
    )
    assert decision == DisputeStatus.AUTO_ACCEPTED
    assert "Transit weight loss" in dec_reason


def test_open_defect_ticket_triggers_fairness_gate():
    """Assert prior open support ticket triggers AUTO_ACCEPT even with full OTP score."""
    telemetry = TelemetryData(
        otp_verified=True,
        geofence_distance_m=20.0,
        shipped_weight_g=500.0,
        delivered_weight_g=500.0,
        defect_ticket_open=True,
    )
    gate = fairness_gate(telemetry, support_tickets=[], policy=policy)
    assert gate.triggered is True
    assert gate.action == "AUTO_ACCEPT"
    assert "Open merchant defect ticket" in gate.reason


def test_prior_complaint_chat_hit_triggers_fairness_gate():
    """Assert prior customer complaint retrieved via RAG triggers AUTO_ACCEPT."""
    telemetry = TelemetryData(
        otp_verified=True,
        geofence_distance_m=25.0,
        shipped_weight_g=500.0,
        delivered_weight_g=500.0,
    )
    chats = [
        ChatHit(
            source="whatsapp",
            text="The screen arrived shattered inside the package",
            score=0.88,
        )
    ]
    gate = fairness_gate(telemetry, support_tickets=chats, policy=policy)
    assert gate.triggered is True
    assert "Prior customer communication verified via whatsapp" in gate.reason
