"""Deterministic Telemetry Audit Engine with Reason-Code Routing & Hybrid Fairness Gate.

Architecture:
  Step 1: Reason-Code Router (OBD / defective merchandise handling)
  Step 2: Omnichannel Fairness Gate (RAG — query prior customer chats)
  Step 3: Deterministic Telemetry Scoring (OTP, GPS ≤100m, Weight, POD, Device)
  Step 4: Consumer Fairness Gate (open ticket / weight loss > 100g)

Scoring Rubric (sums to max 100):
  ┌───────────────────────┬────────┬───────────────────────────────────────────┐
  │ Signal                │ Weight │ Logic                                     │
  ├───────────────────────┼────────┼───────────────────────────────────────────┤
  │ OTP Verified          │  35    │ Binary — was delivery OTP matched?        │
  │ Geofence Match        │  30    │ ≤100m full / 100-500m 80% / 500-2km fall  │
  │ Weight Delta OK       │  20    │ Origin-to-delivery weight within 5%       │
  │ Delivery Signature    │  10    │ Binary — POD / signature exists           │
  │ Device Fingerprint    │   5    │ Device matches checkout session           │
  └───────────────────────┴────────┴───────────────────────────────────────────┘

Reason-Code Routing:
  - defective_merchandise + STANDARD: OTP/GPS irrelevant → NEEDS_REVIEW
  - defective_merchandise + OPEN_BOX:  OTP proves inspection → AUTO_CONTESTED

Thresholds:
  - Score > 80  → AUTO_CONTESTED
  - Score 40-80 → NEEDS_REVIEW
  - Score < 40  → AUTO_ACCEPTED
"""

import json
import logging
from typing import Any, Dict, Tuple, Optional
from core.models import DisputeStatus
from core.schemas import AuditBreakdown
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

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


def _extract_geofence_meters(telemetry: Dict[str, Any]) -> Optional[float]:
    """Extract geofence distance in meters from telemetry.

    Checks for meters field first, falls back to km conversion.
    """
    # Direct meters field
    geo_m = telemetry.get("geofence_distance_m")
    if geo_m is not None:
        try:
            return float(geo_m)
        except (ValueError, TypeError):
            pass

    # Nested geofence object with meters
    geo_data = telemetry.get("geofence", {})
    if isinstance(geo_data, dict):
        if geo_data.get("distance_m") is not None:
            try:
                return float(geo_data["distance_m"])
            except (ValueError, TypeError):
                pass
        # Fall back to km → convert to meters
        if geo_data.get("distance_km") is not None:
            try:
                return float(geo_data["distance_km"]) * 1000.0
            except (ValueError, TypeError):
                pass

    # Top-level km fallback
    geo_km = telemetry.get("geofence_distance_km")
    if geo_km is not None:
        try:
            return float(geo_km) * 1000.0
        except (ValueError, TypeError):
            pass

    return None


def evaluate_telemetry(
    raw_telemetry: str | None,
    delivery_type: str = "STANDARD",
    reason_code: str | None = None,
    rag_fairness_triggered: bool = False,
    rag_fairness_summary: str | None = None,
    policy_checklist_json: str | None = None,
) -> AuditBreakdown:
    """Run full deterministic audit evaluation with reason-code routing and hybrid gates.

    Returns an AuditBreakdown schema with points, metrics, and final decision.
    """
    telemetry = _safe_parse_telemetry(raw_telemetry)
    dt = (delivery_type or telemetry.get("delivery_type", "STANDARD")).upper()
    rc = (reason_code or telemetry.get("reason_code", "product_not_received")).lower()

    # ── 0. Reason-Code Routing (Pre-Scoring) ─────────────────────────────────
    reason_code_route = None
    skip_otp_gps = False

    if rc == "defective_merchandise" and dt == "STANDARD":
        # Standard delivery + defective claim: OTP/GPS won't help, customer might be right
        reason_code_route = "DEFECTIVE_STANDARD_SKIP_TELEMETRY"
        skip_otp_gps = True
    elif rc == "defective_merchandise" and dt == "OPEN_BOX":
        # OBD: OTP legally proves physical inspection before acceptance
        reason_code_route = "OBD_DEFECTIVE_OVERRIDE"

    # ── 1. Check Consumer Fairness Gate (Deterministic) ────────────────────────
    defect_ticket_open = False
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

    if skip_otp_gps:
        otp_points = 0.0  # OTP irrelevant for standard defective merchandise
    else:
        otp_points = WEIGHTS["otp_verified"] if otp_verified else 0.0

    # B. Geofence Distance — Meter Precision (30 pts)
    geofence_m = _extract_geofence_meters(telemetry)
    geofence_km = geofence_m / 1000.0 if geofence_m is not None else None

    geofence_points = 0.0
    if skip_otp_gps:
        geofence_points = 0.0  # GPS irrelevant for standard defective merchandise
    elif geofence_m is not None:
        primary = settings.geofence_primary_radius_m    # 100m
        secondary = settings.geofence_secondary_radius_m  # 500m
        tertiary = settings.geofence_tertiary_radius_m   # 2000m

        if geofence_m <= primary:
            geofence_points = WEIGHTS["geofence_match"]  # Full 30 pts
        elif geofence_m <= secondary:
            geofence_points = round(WEIGHTS["geofence_match"] * 0.80, 2)  # 24 pts
        elif geofence_m <= tertiary:
            # Linear falloff from 500m to 2000m
            ratio = 1.0 - ((geofence_m - secondary) / (tertiary - secondary))
            geofence_points = round(WEIGHTS["geofence_match"] * 0.80 * max(0.0, ratio), 2)
        else:
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

    # ── 4. Decision Logic with Hybrid Gates ─────────────────────────────────

    # Priority 1: RAG fairness gate (prior genuine complaint in omnichannel chats)
    if rag_fairness_triggered:
        decision = DisputeStatus.AUTO_ACCEPTED
        if not fairness_reason:
            fairness_reason = "RAG Omnichannel Fairness Gate: Genuine prior complaint detected in customer communications"
        fairness_triggered = True

    # Priority 2: Deterministic fairness gate (open ticket / weight loss)
    elif fairness_triggered:
        decision = DisputeStatus.AUTO_ACCEPTED

    # Priority 3: Reason-code routing for standard defective merchandise
    elif reason_code_route == "DEFECTIVE_STANDARD_SKIP_TELEMETRY":
        # OTP/GPS skipped — route to NEEDS_REVIEW regardless of score
        decision = DisputeStatus.NEEDS_REVIEW

    # Priority 4: OBD override for defective merchandise
    elif reason_code_route == "OBD_DEFECTIVE_OVERRIDE" and otp_verified:
        # OBD + OTP verified = customer inspected and accepted
        decision = DisputeStatus.AUTO_CONTESTED

    # Priority 5: Standard score-based thresholds
    elif confidence_score > 80.0:
        decision = DisputeStatus.AUTO_CONTESTED
    elif confidence_score >= 40.0:
        decision = DisputeStatus.NEEDS_REVIEW
    else:
        decision = DisputeStatus.AUTO_ACCEPTED

    return AuditBreakdown(
        confidence_score=confidence_score,
        decision=decision,
        delivery_type=dt,
        reason_code_route=reason_code_route,
        otp_verified=otp_verified,
        otp_points=otp_points,
        geofence_distance_km=geofence_km,
        geofence_distance_m=geofence_m,
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
        rag_fairness_triggered=rag_fairness_triggered,
        rag_fairness_summary=rag_fairness_summary,
        policy_checklist_json=policy_checklist_json,
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
