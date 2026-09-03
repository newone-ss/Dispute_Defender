"""Deterministic Telemetry Audit Engine & Consumer Fairness Gate.

Scoring Rubric (sums to max 100):
  ┌───────────────────────┬────────┬───────────────────────────────────────────┐
  │ Signal                │ Weight │ Logic                                     │
  ├───────────────────────┼────────┼───────────────────────────────────────────┤
  │ OTP Verified          │  35    │ Binary — was delivery OTP matched?        │
  │ Geofence Match        │  30    │ Delivery GPS within 5km of address        │
  │ Weight Delta OK       │  20    │ Origin-to-delivery weight within 5%       │
  │ Delivery Signature    │  10    │ Binary — POD / signature exists           │
  │ Device Fingerprint    │   5    │ Device matches checkout session           │
  └───────────────────────┴────────┴───────────────────────────────────────────┘

Consumer Fairness Gate:
  - If customer defect ticket is OPEN or transit weight loss > 100g,
    the transaction is flagged as a genuine merchant/courier failure.
    Output: DECISION = AUTO_ACCEPT (avoiding the ₹1,500 bank penalty fee).

Thresholds:
  - Score > 80  → AUTO_CONTESTED
  - Score 40-80 → NEEDS_REVIEW
  - Score < 40  → AUTO_ACCEPTED
"""

import json
import logging
from typing import Any, Dict, Tuple
from core.models import DisputeStatus
from core.schemas import AuditBreakdown

logger = logging.getLogger(__name__)

WEIGHTS = {
    "otp_verified": 35.0,
    "geofence_match": 30.0,
    "weight_delta_ok": 20.0,
    "delivery_signature": 10.0,
    "device_fingerprint": 5.0,
}


def _safe_parse_telemetry(raw: str | None) -> Dict[str, Any]:
    """Safely parse the raw_telemetry JSON blob, returning empty dict on failure."""
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, TypeError):
        logger.warning("Failed to parse raw_telemetry JSON")
        return {}


def evaluate_telemetry(raw_telemetry: str | None) -> AuditBreakdown:
    """Run full deterministic audit evaluation on telemetry signals and fairness gates.

    Returns an AuditBreakdown schema with points, metrics, and final decision.
    """
    telemetry = _safe_parse_telemetry(raw_telemetry)

    # ── 1. Check Consumer Fairness Gate ─────────────────────────────────────
    defect_ticket_open = False
    # Check ticket signals in different possible payload formats
    if telemetry.get("defect_ticket_open") is True or telemetry.get("customer_ticket_open") is True:
        defect_ticket_open = True
    elif isinstance(telemetry.get("support_ticket"), dict):
        ticket = telemetry["support_ticket"]
        if ticket.get("open") is True or str(ticket.get("status", "")).lower() in ["open", "pending", "escalated"]:
            defect_ticket_open = True
    elif str(telemetry.get("ticket_status", "")).lower() in ["open", "pending", "escalated"]:
        defect_ticket_open = True

    # Weight telemetry extraction
    weight_data = telemetry.get("weight", {})
    shipped_g = None
    delivered_g = None
    if isinstance(weight_data, dict):
        shipped_g = weight_data.get("shipped_g")
        delivered_g = weight_data.get("delivered_g")
    if shipped_g is None:
        shipped_g = telemetry.get("shipped_weight_g")
    if delivered_g is None:
        delivered_g = telemetry.get("delivered_weight_g")

    shipped_val = float(shipped_g) if shipped_g is not None else None
    delivered_val = float(delivered_g) if delivered_g is not None else None

    weight_loss_g = 0.0
    if shipped_val is not None and delivered_val is not None:
        weight_loss_g = max(0.0, shipped_val - delivered_val)

    # Fairness Gate Check: open defect ticket OR weight loss > 100g
    fairness_triggered = False
    fairness_reason = None

    if defect_ticket_open:
        fairness_triggered = True
        fairness_reason = "Open customer defect/support ticket active on order"
    elif weight_loss_g > 100.0:
        fairness_triggered = True
        fairness_reason = f"Transit weight loss ({weight_loss_g:.1f}g > 100g threshold) indicates missing/damaged contents"

    # ── 2. Telemetry Signal Scoring ──────────────────────────────────────────

    # A. OTP Verified (Binary: 35 pts)
    otp_data = telemetry.get("otp", {})
    otp_verified = False
    if isinstance(otp_data, dict) and otp_data.get("verified") is True:
        otp_verified = True
    elif telemetry.get("otp_verified") is True:
        otp_verified = True
    otp_points = WEIGHTS["otp_verified"] if otp_verified else 0.0

    # B. Geofence Distance (30 pts)
    geo_data = telemetry.get("geofence", {})
    geo_distance = None
    if isinstance(geo_data, dict):
        geo_distance = geo_data.get("distance_km")
    if geo_distance is None:
        geo_distance = telemetry.get("geofence_distance_km")

    geofence_dist_val = None
    geofence_points = 0.0
    if geo_distance is not None:
        try:
            geofence_dist_val = float(geo_distance)
            if geofence_dist_val <= 5.0:
                geofence_points = WEIGHTS["geofence_match"]
            elif geofence_dist_val <= 15.0:
                # Linear falloff from 5km to 15km
                ratio = 1.0 - ((geofence_dist_val - 5.0) / 10.0)
                geofence_points = round(WEIGHTS["geofence_match"] * max(0.0, ratio), 2)
            else:
                geofence_points = 0.0
        except (ValueError, TypeError):
            geofence_points = 0.0

    # C. Weight Delta (20 pts)
    weight_points = 0.0
    if shipped_val is not None and delivered_val is not None and shipped_val > 0:
        delta_pct = abs(shipped_val - delivered_val) / shipped_val * 100.0
        if delta_pct <= 5.0:
            weight_points = WEIGHTS["weight_delta_ok"]
        elif delta_pct <= 15.0:
            ratio = 1.0 - ((delta_pct - 5.0) / 10.0)
            weight_points = round(WEIGHTS["weight_delta_ok"] * max(0.0, ratio), 2)
        else:
            weight_points = 0.0

    # D. Delivery Signature / POD (10 pts)
    signature_present = False
    if telemetry.get("delivery_signature") is True:
        signature_present = True
    elif isinstance(telemetry.get("pod"), dict) and telemetry["pod"].get("exists") is True:
        signature_present = True
    elif isinstance(telemetry.get("manifest"), dict) and telemetry["manifest"].get("signature_present") is True:
        signature_present = True
    signature_points = WEIGHTS["delivery_signature"] if signature_present else 0.0

    # E. Device Fingerprint (5 pts)
    device_match = False
    if telemetry.get("device_fingerprint_match") is True:
        device_match = True
    elif isinstance(telemetry.get("device"), dict) and telemetry["device"].get("fingerprint_match") is True:
        device_match = True
    device_points = WEIGHTS["device_fingerprint"] if device_match else 0.0

    # ── 3. Total Score & Action Decision ────────────────────────────────────
    raw_total = otp_points + geofence_points + weight_points + signature_points + device_points
    confidence_score = min(round(raw_total, 2), 100.0)

    # Fairness gate overrides score
    if fairness_triggered:
        decision = DisputeStatus.AUTO_ACCEPTED
    elif confidence_score > 80.0:
        decision = DisputeStatus.AUTO_CONTESTED
    elif confidence_score >= 40.0:
        decision = DisputeStatus.NEEDS_REVIEW
    else:
        decision = DisputeStatus.AUTO_ACCEPTED

    return AuditBreakdown(
        confidence_score=confidence_score,
        decision=decision,
        otp_verified=otp_verified,
        otp_points=otp_points,
        geofence_distance_km=geofence_dist_val,
        geofence_points=geofence_points,
        shipped_weight_g=shipped_val,
        delivered_weight_g=delivered_val,
        weight_loss_g=weight_loss_g,
        weight_points=weight_points,
        delivery_signature=signature_present,
        signature_points=signature_points,
        device_fingerprint_match=device_match,
        device_points=device_points,
        fairness_gate_triggered=fairness_triggered,
        fairness_reason=fairness_reason,
    )


def calculate_confidence(raw_telemetry: str | None) -> float:
    """Convenience helper to extract numeric confidence score."""
    breakdown = evaluate_telemetry(raw_telemetry)
    return breakdown.confidence_score


def decide_action(confidence_or_breakdown: float | AuditBreakdown) -> DisputeStatus:
    """Map a confidence score or AuditBreakdown to a DisputeStatus."""
    if isinstance(confidence_or_breakdown, AuditBreakdown):
        return confidence_or_breakdown.decision

    score = float(confidence_or_breakdown)
    if score > 80.0:
        return DisputeStatus.AUTO_CONTESTED
    elif score >= 40.0:
        return DisputeStatus.NEEDS_REVIEW
    else:
        return DisputeStatus.AUTO_ACCEPTED
