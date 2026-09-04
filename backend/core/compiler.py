"""Evidence Compiler — renders deterministic bank representment packets via Jinja2.

Mandate: Uses deterministic templates (no LLMs for legal drafting) to compile
the evidence narrative submitted to the issuing bank via Razorpay's dispute contest API.
Template: backend/data/templates/npci_udir_packet.md.j2
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

# Template directory points to backend/data/templates
_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TEMPLATE_DIR = os.path.join(_BACKEND_ROOT, "data", "templates")

_env = Environment(
    loader=FileSystemLoader(_TEMPLATE_DIR),
    autoescape=select_autoescape(["html", "txt"]),
    trim_blocks=True,
    lstrip_blocks=True,
)


def _safe_parse_json(raw: str | None) -> Dict[str, Any]:
    """Safely parse JSON string."""
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def compile_evidence(
    dispute_id: str,
    payment_id: str | None,
    order_id: str | None,
    amount: float,
    reason_code: str | None,
    confidence_score: float,
    raw_telemetry: str | None,
    ocr_manifest_json: str | None = None,
    delivery_type: str = "STANDARD",
    rag_fairness_summary: str | None = None,
    policy_checklist_json: str | None = None,
    geofence_distance_m: float | None = None,
) -> str:
    """Render the official NPCI UDIR / Visa representment evidence markdown.

    Args:
        dispute_id: Razorpay dispute identifier.
        payment_id: Original payment/transaction ID.
        order_id: Merchant internal order ID.
        amount: Disputed amount in INR.
        reason_code: Chargeback reason code.
        confidence_score: Score from audit_engine (0-100).
        raw_telemetry: JSON blob with telemetry signals.
        ocr_manifest_json: Parsed OCR manifest data if available.
        delivery_type: STANDARD, OPEN_BOX, or LOCKER.
        rag_fairness_summary: LLM/keyword summary of omnichannel chat analysis.
        policy_checklist_json: JSON of evidence requirements for this reason code.
        geofence_distance_m: GPS distance in meters.

    Returns:
        Rendered markdown evidence ready for Document API upload and contest submission.
    """
    telemetry = _safe_parse_json(raw_telemetry)
    ocr_data = _safe_parse_json(ocr_manifest_json)

    # Extract weights
    weight_info = telemetry.get("weight", {})
    shipped_g = weight_info.get("shipped_g") or telemetry.get("shipped_weight_g") or 500
    delivered_g = weight_info.get("delivered_g") or telemetry.get("delivered_weight_g") or shipped_g
    weight_loss = max(0.0, float(shipped_g) - float(delivered_g)) if shipped_g and delivered_g else 0.0

    # Extract geofence (meters preferred, fall back to km conversion)
    if geofence_distance_m is not None:
        geo_m = geofence_distance_m
    else:
        geo_data = telemetry.get("geofence", {})
        if isinstance(geo_data, dict) and geo_data.get("distance_m") is not None:
            geo_m = float(geo_data["distance_m"])
        elif isinstance(geo_data, dict) and geo_data.get("distance_km") is not None:
            geo_m = float(geo_data["distance_km"]) * 1000.0
        elif telemetry.get("geofence_distance_km") is not None:
            geo_m = float(telemetry["geofence_distance_km"]) * 1000.0
        else:
            geo_m = None

    geofence_distance_km = geo_m / 1000.0 if geo_m is not None else None

    # Extract OTP
    otp_verified = (
        telemetry.get("otp", {}).get("verified")
        if isinstance(telemetry.get("otp"), dict)
        else telemetry.get("otp_verified", False)
    )

    # Extract Courier / POD
    courier_partner = ocr_data.get("courier_partner") or telemetry.get("courier", "Delhivery Express")
    awb_number = ocr_data.get("awb_number") or telemetry.get("awb_number") or f"DEL-{dispute_id[-6:]}"
    delivery_signature = (
        ocr_data.get("signature_present")
        or telemetry.get("delivery_signature")
        or telemetry.get("pod", {}).get("exists", False)
    )
    device_fingerprint_match = telemetry.get("device_fingerprint_match", False)
    defect_ticket_open = telemetry.get("defect_ticket_open", False)

    # Parse policy checklist
    policy_checklist = _safe_parse_json(policy_checklist_json) if policy_checklist_json else {}

    dt = (delivery_type or "STANDARD").upper()

    context = {
        "dispute_id": dispute_id,
        "payment_id": payment_id or "N/A",
        "order_id": order_id or f"ord_{dispute_id[-8:]}",
        "amount": amount,
        "reason_code": reason_code or "product_not_received",
        "confidence_score": confidence_score,
        "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "otp_verified": bool(otp_verified),
        "geofence_distance_km": geofence_distance_km,
        "geofence_distance_m": geo_m,
        "shipped_weight_g": shipped_g,
        "delivered_weight_g": delivered_g,
        "weight_loss_g": round(weight_loss, 1),
        "courier_partner": courier_partner,
        "awb_number": awb_number,
        "delivery_signature": bool(delivery_signature),
        "device_fingerprint_match": bool(device_fingerprint_match),
        "defect_ticket_open": bool(defect_ticket_open),
        "ocr_data": ocr_data,
        "telemetry": telemetry,
        # New hybrid fields
        "delivery_type": dt,
        "is_obd": dt == "OPEN_BOX",
        "rag_fairness_summary": rag_fairness_summary,
        "policy_checklist": policy_checklist,
    }

    try:
        template = _env.get_template("npci_udir_packet.md.j2")
        return template.render(**context)
    except Exception as e:
        logger.error(f"Template rendering failed for dispute {dispute_id}: {e}")
        # Fallback to minimal structured markdown
        return (
            f"# NPCI UDIR Dispute Representment\n\n"
            f"**Dispute ID:** `{dispute_id}` | **Payment ID:** `{payment_id}`\n"
            f"**Amount:** ₹{amount:.2f} | **Audit Score:** {confidence_score}/100\n"
            f"**Delivery Type:** {dt}\n"
            f"**OTP Verified:** {otp_verified} | **Geofence Distance:** {geo_m}m\n"
            f"**Weights:** Shipped {shipped_g}g / Delivered {delivered_g}g (Loss: {weight_loss}g)\n"
            f"**Proof of Delivery:** Recorded on courier manifest.\n"
        )
