"""Seeds SQLite with 50 diverse synthetic dispute test cases.

Categories (50 total):
- 30 Winnable Legitimate Delivery cases (Score > 80 → AUTO_CONTESTED)
- 10 Genuine Customer Defect / Loss cases (Fairness Gate → AUTO_ACCEPTED)
- 10 Ambiguous or Fraud cases (5 NEEDS_REVIEW, 5 AUTO_ACCEPTED)
"""

import json
import logging
import os
import random
import sys
from datetime import datetime, timedelta

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import init_db, SessionLocal
from core.models import Dispute, DisputeStatus
from core.audit_engine import evaluate_telemetry
from core.compiler import compile_evidence
from core.ocr_extractor import generate_mock_manifest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_db")

REASONS = [
    "product_not_received",
    "fraudulent_transaction",
    "goods_damaged",
    "subscription_unauthorized",
    "duplicate_billing",
    "credit_not_issued",
]

COURIERS = ["Delhivery Express", "Blue Dart", "Shadowfax", "Ecom Express", "XpressBees"]


def generate_seed_cases() -> list[dict]:
    cases = []
    base_time = datetime.utcnow() - timedelta(days=14)

    # ── 1. 30 Winnable Cases (Legitimate Deliveries, Score > 80) ───────────────
    for i in range(1, 31):
        disp_id = f"disp_win_{i:03d}"
        pay_id = f"pay_win_{i:03d}"
        ord_id = f"ord_win_{i:03d}"
        amount = round(random.uniform(1500.0, 32000.0), 2)
        courier = random.choice(COURIERS)
        shipped_g = round(random.uniform(400.0, 1800.0), 1)
        delivered_g = round(shipped_g + random.uniform(-10.0, 5.0), 1)
        dist_km = round(random.uniform(0.1, 3.2), 2)
        created_at = base_time + timedelta(hours=i * 6, minutes=random.randint(5, 55))

        mock_manifest = generate_mock_manifest(courier=courier, weight_g=delivered_g, with_signature=True)

        telemetry = {
            "otp": {"verified": True, "timestamp": (created_at + timedelta(days=2)).isoformat()},
            "otp_verified": True,
            "geofence": {"distance_km": dist_km, "target_lat": 12.9716, "delivery_lat": 12.9721},
            "geofence_distance_km": dist_km,
            "weight": {"shipped_g": shipped_g, "delivered_g": delivered_g},
            "shipped_weight_g": shipped_g,
            "delivered_weight_g": delivered_g,
            "delivery_signature": True,
            "device_fingerprint_match": True,
            "defect_ticket_open": False,
            "courier": courier,
            "awb_number": mock_manifest.awb_number,
            "manifest_ocr_text": mock_manifest.raw_extracted_text,
        }

        cases.append({
            "dispute_id": disp_id,
            "payment_id": pay_id,
            "order_id": ord_id,
            "amount": amount,
            "reason_code": "product_not_received",
            "telemetry": telemetry,
            "ocr_manifest": mock_manifest.model_dump_json(),
            "created_at": created_at,
            "category": "winnable",
        })

    # ── 2. 10 Genuine Customer Defects / Transit Loss Cases (Fairness Gate) ───
    for i in range(1, 11):
        disp_id = f"disp_defect_{i:03d}"
        pay_id = f"pay_defect_{i:03d}"
        ord_id = f"ord_defect_{i:03d}"
        amount = round(random.uniform(2200.0, 18000.0), 2)
        courier = random.choice(COURIERS)
        created_at = base_time + timedelta(hours=180 + i * 8)

        # 5 cases with open defect support ticket, 5 cases with >100g transit loss
        if i <= 5:
            shipped_g = 800.0
            delivered_g = 795.0
            telemetry = {
                "otp": {"verified": True},
                "geofence": {"distance_km": 0.8},
                "weight": {"shipped_g": shipped_g, "delivered_g": delivered_g},
                "delivery_signature": True,
                "defect_ticket_open": True,
                "support_ticket": {
                    "open": True,
                    "ticket_id": f"TICK-{1000 + i}",
                    "issue": "Item arrived broken with shattered screen",
                },
                "courier": courier,
            }
        else:
            shipped_g = 1200.0
            delivered_g = 950.0  # 250g weight loss > 100g
            telemetry = {
                "otp": {"verified": True},
                "geofence": {"distance_km": 1.2},
                "weight": {"shipped_g": shipped_g, "delivered_g": delivered_g},
                "delivery_signature": True,
                "defect_ticket_open": False,
                "courier": courier,
            }

        mock_manifest = generate_mock_manifest(courier=courier, weight_g=delivered_g, with_signature=True)

        cases.append({
            "dispute_id": disp_id,
            "payment_id": pay_id,
            "order_id": ord_id,
            "amount": amount,
            "reason_code": "goods_damaged" if i <= 5 else "product_unacceptable",
            "telemetry": telemetry,
            "ocr_manifest": mock_manifest.model_dump_json(),
            "created_at": created_at,
            "category": "customer_defect_auto_accept",
        })

    # ── 3. 10 Ambiguous or High-Risk Cases (5 NEEDS_REVIEW, 5 AUTO_ACCEPTED) ──
    for i in range(1, 11):
        disp_id = f"disp_edge_{i:03d}"
        pay_id = f"pay_edge_{i:03d}"
        ord_id = f"ord_edge_{i:03d}"
        amount = round(random.uniform(900.0, 14000.0), 2)
        courier = random.choice(COURIERS)
        created_at = base_time + timedelta(hours=260 + i * 6)

        if i <= 5:
            # Medium confidence (score 40-75) -> NEEDS_REVIEW
            dist_km = round(random.uniform(7.0, 11.5), 1)
            telemetry = {
                "otp": {"verified": False},
                "geofence": {"distance_km": dist_km},
                "weight": {"shipped_g": 600, "delivered_g": 590},
                "delivery_signature": True,
                "device_fingerprint_match": False,
                "defect_ticket_open": False,
                "courier": courier,
            }
        else:
            # Low confidence (score < 40) -> AUTO_ACCEPTED
            dist_km = round(random.uniform(25.0, 85.0), 1)
            telemetry = {
                "otp": {"verified": False},
                "geofence": {"distance_km": dist_km},
                "weight": {"shipped_g": 600, "delivered_g": 0},
                "delivery_signature": False,
                "device_fingerprint_match": False,
                "defect_ticket_open": False,
                "courier": courier,
            }

        mock_manifest = generate_mock_manifest(courier=courier, weight_g=590.0 if i <= 5 else 0.0, with_signature=(i <= 5))

        cases.append({
            "dispute_id": disp_id,
            "payment_id": pay_id,
            "order_id": ord_id,
            "amount": amount,
            "reason_code": "fraudulent_transaction",
            "telemetry": telemetry,
            "ocr_manifest": mock_manifest.model_dump_json(),
            "created_at": created_at,
            "category": "ambiguous_or_fraud",
        })

    return cases


def seed_database():
    """Populate SQLite database with synthetic records."""
    logger.info("Initializing database tables...")
    init_db()

    db = SessionLocal()
    try:
        # Clear existing seeded rows for idempotent reset
        db.query(Dispute).delete()
        db.commit()

        cases = generate_seed_cases()
        logger.info(f"Generating {len(cases)} synthetic dispute records...")

        for c in cases:
            raw_json = json.dumps(c["telemetry"])
            audit = evaluate_telemetry(raw_json)

            evidence = compile_evidence(
                dispute_id=c["dispute_id"],
                payment_id=c["payment_id"],
                order_id=c["order_id"],
                amount=c["amount"],
                reason_code=c["reason_code"],
                confidence_score=audit.confidence_score,
                raw_telemetry=raw_json,
                ocr_manifest_json=c["ocr_manifest"],
            )

            doc_id = f"doc_seed_{c['dispute_id'][-6:]}" if audit.decision == DisputeStatus.AUTO_CONTESTED else None

            dispute = Dispute(
                dispute_id=c["dispute_id"],
                payment_id=c["payment_id"],
                order_id=c["order_id"],
                status=audit.decision,
                reason_code=c["reason_code"],
                amount=c["amount"],
                confidence_score=audit.confidence_score,
                otp_verified=audit.otp_verified,
                geofence_distance_km=audit.geofence_distance_km,
                shipped_weight_g=audit.shipped_weight_g,
                delivered_weight_g=audit.delivered_weight_g,
                weight_loss_g=audit.weight_loss_g,
                defect_ticket_open=c["telemetry"].get("defect_ticket_open", False),
                fairness_gate_triggered=audit.fairness_gate_triggered,
                fairness_reason=audit.fairness_reason,
                evidence_text=evidence,
                document_id=doc_id,
                ocr_manifest_json=c["ocr_manifest"],
                raw_telemetry=raw_json,
                created_at=c["created_at"],
            )
            db.add(dispute)

        db.commit()
        logger.info(f"✅ Successfully seeded {len(cases)} dispute cases into SQLite!")

    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
