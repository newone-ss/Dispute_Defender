"""Seeds SQLite with 50 diverse synthetic dispute test cases and ChromaDB with mock data.

Categories (50 total):
- 25 Winnable Legitimate Delivery cases (Score > 80 → AUTO_CONTESTED)
- 5 OBD Clean Delivery cases (delivery_type=OPEN_BOX → AUTO_CONTESTED)
- 5 OBD Defective Merchandise cases (OBD + defective → AUTO_CONTESTED via OBD override)
- 5 Genuine Customer Defect / Loss cases (Fairness Gate → AUTO_ACCEPTED)
- 5 RAG Prior Complaint cases (RAG fairness gate → AUTO_ACCEPTED)
- 5 Ambiguous or Fraud cases (NEEDS_REVIEW / AUTO_ACCEPTED)

ChromaDB Seeding:
- Policy documents from knowledge_base/ directory
- 20 mock omnichannel chat transcripts (WhatsApp, Email, Zendesk)
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
from core.doc_loader import get_chroma_client, load_policy_documents, load_customer_chats, reset_collections
from core.policy_rag import get_policy_checklist

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_db")

REASONS = [
    "product_not_received",
    "fraudulent_transaction",
    "defective_merchandise",
    "subscription_unauthorized",
    "duplicate_billing",
    "credit_not_issued",
]

COURIERS = ["Delhivery Express", "Blue Dart", "Shadowfax", "Ecom Express", "XpressBees"]


def _generate_mock_chats():
    """Generate 20 mock omnichannel chat transcripts for ChromaDB seeding."""
    chats = []

    # 5 genuine complaint chats (linked to RAG dispute IDs)
    complaints = [
        {
            "dispute_id": "disp_rag_001", "order_id": "ord_rag_001",
            "channel": "whatsapp", "customer_name": "Rahul Sharma",
            "timestamp": "2026-08-28T14:30:00",
            "message": "Hi, I received my order today but the laptop screen is completely cracked and shattered. The box looked fine from outside but the product inside is totally broken. I need a refund or replacement urgently.",
        },
        {
            "dispute_id": "disp_rag_002", "order_id": "ord_rag_002",
            "channel": "email", "customer_name": "Priya Patel",
            "timestamp": "2026-08-29T09:15:00",
            "message": "Subject: Wrong item received — Order ord_rag_002. I ordered a blue wireless headphone but received a completely different product — a phone case. This is not what I ordered. The item is wrong and I want my money back.",
        },
        {
            "dispute_id": "disp_rag_003", "order_id": "ord_rag_003",
            "channel": "zendesk", "customer_name": "Amit Kumar",
            "timestamp": "2026-08-30T16:45:00",
            "message": "Ticket #ZD-4420: Product defective — the power bank I received is not working at all. It doesn't charge and the LED indicator is dead on arrival. I've tried multiple cables. This product is defective and I need a return.",
        },
        {
            "dispute_id": "disp_rag_004", "order_id": "ord_rag_004",
            "channel": "whatsapp", "customer_name": "Sneha Reddy",
            "timestamp": "2026-08-31T11:20:00",
            "message": "The dress I received has missing buttons and a torn seam. The quality is terrible and unacceptable. This is not as described on your website. I want a full refund please.",
        },
        {
            "dispute_id": "disp_rag_005", "order_id": "ord_rag_005",
            "channel": "email", "customer_name": "Vikram Singh",
            "timestamp": "2026-09-01T08:00:00",
            "message": "Subject: Damaged item — my order arrived with the ceramic vase completely broken into pieces inside the box. The packaging was inadequate and the product is damaged beyond use. I need replacement or refund.",
        },
    ]

    # 15 non-complaint chats (general inquiries, tracking, happy customers)
    non_complaints = [
        {"dispute_id": "disp_win_001", "order_id": "ord_win_001", "channel": "whatsapp",
         "message": "Hi, can you share the tracking number for my order? I placed it yesterday.", "timestamp": "2026-08-25T10:00:00"},
        {"dispute_id": "disp_win_002", "order_id": "ord_win_002", "channel": "email",
         "message": "Thank you for the quick delivery! The product looks great. Very happy with my purchase.", "timestamp": "2026-08-26T14:30:00"},
        {"dispute_id": "disp_win_003", "order_id": "ord_win_003", "channel": "whatsapp",
         "message": "When will my order be delivered? It's been 3 days since I placed it.", "timestamp": "2026-08-27T09:15:00"},
        {"dispute_id": "disp_win_004", "order_id": "ord_win_004", "channel": "zendesk",
         "message": "I want to change the delivery address for my order. Can you update it?", "timestamp": "2026-08-28T11:00:00"},
        {"dispute_id": "disp_win_005", "order_id": "ord_win_005", "channel": "email",
         "message": "Do you have this product in a different color? I'm interested in the black variant.", "timestamp": "2026-08-29T16:20:00"},
        {"dispute_id": "disp_win_006", "order_id": "ord_win_006", "channel": "whatsapp",
         "message": "Received my package. Everything looks perfect. Thanks!", "timestamp": "2026-08-30T12:00:00"},
        {"dispute_id": "disp_win_007", "order_id": "ord_win_007", "channel": "whatsapp",
         "message": "Can I get an invoice copy for my order? I need it for reimbursement.", "timestamp": "2026-09-01T10:30:00"},
        {"dispute_id": "disp_win_008", "order_id": "ord_win_008", "channel": "email",
         "message": "Is there a discount code available for my next purchase? I'm a returning customer.", "timestamp": "2026-08-26T15:45:00"},
        {"dispute_id": "disp_win_009", "order_id": "ord_win_009", "channel": "zendesk",
         "message": "The delivery was slightly late but the product quality is excellent. No complaints.", "timestamp": "2026-08-27T17:00:00"},
        {"dispute_id": "disp_win_010", "order_id": "ord_win_010", "channel": "whatsapp",
         "message": "What is your return policy? I just want to understand before buying.", "timestamp": "2026-08-28T14:00:00"},
        {"dispute_id": "disp_edge_001", "order_id": "ord_edge_001", "channel": "email",
         "message": "I'm not sure if this is the right size. Can I exchange it? Haven't opened yet.", "timestamp": "2026-08-29T13:30:00"},
        {"dispute_id": "disp_edge_002", "order_id": "ord_edge_002", "channel": "whatsapp",
         "message": "I changed my mind about the purchase. Can I cancel? Haven't received it yet.", "timestamp": "2026-08-30T10:00:00"},
        {"dispute_id": "disp_edge_003", "order_id": "ord_edge_003", "channel": "zendesk",
         "message": "The product is fine but I found a better price elsewhere. Can I get a price match?", "timestamp": "2026-08-31T15:00:00"},
        {"dispute_id": "disp_defect_001", "order_id": "ord_defect_001", "channel": "whatsapp",
         "message": "Thank you for processing my replacement. I appreciate the quick response.", "timestamp": "2026-09-01T11:00:00"},
        {"dispute_id": "disp_defect_002", "order_id": "ord_defect_002", "channel": "email",
         "message": "My order was delivered on time. The packaging could be better but the product is fine.", "timestamp": "2026-09-02T09:00:00"},
    ]

    chats.extend(complaints)
    chats.extend(non_complaints)
    return chats


def generate_seed_cases() -> list[dict]:
    cases = []
    base_time = datetime.utcnow() - timedelta(days=14)

    # ── 1. 25 Winnable Cases (Legitimate Deliveries, Score > 80) ───────────────
    for i in range(1, 26):
        disp_id = f"disp_win_{i:03d}"
        pay_id = f"pay_win_{i:03d}"
        ord_id = f"ord_win_{i:03d}"
        amount = round(random.uniform(1500.0, 32000.0), 2)
        courier = random.choice(COURIERS)
        shipped_g = round(random.uniform(400.0, 1800.0), 1)
        delivered_g = round(shipped_g + random.uniform(-10.0, 5.0), 1)
        dist_km = round(random.uniform(0.01, 0.08), 3)  # 10-80 meters
        created_at = base_time + timedelta(hours=i * 6, minutes=random.randint(5, 55))

        mock_manifest = generate_mock_manifest(courier=courier, weight_g=delivered_g, with_signature=True)

        telemetry = {
            "otp": {"verified": True, "timestamp": (created_at + timedelta(days=2)).isoformat()},
            "otp_verified": True,
            "geofence": {"distance_km": dist_km},
            "geofence_distance_km": dist_km,
            "weight": {"shipped_g": shipped_g, "delivered_g": delivered_g},
            "shipped_weight_g": shipped_g,
            "delivered_weight_g": delivered_g,
            "delivery_signature": True,
            "device_fingerprint_match": True,
            "defect_ticket_open": False,
            "courier": courier,
            "awb_number": mock_manifest.awb_number,
            "delivery_type": "STANDARD",
            "manifest_ocr_text": mock_manifest.raw_extracted_text,
        }

        cases.append({
            "dispute_id": disp_id, "payment_id": pay_id, "order_id": ord_id,
            "amount": amount, "reason_code": "product_not_received",
            "delivery_type": "STANDARD",
            "telemetry": telemetry, "ocr_manifest": mock_manifest.model_dump_json(),
            "created_at": created_at, "category": "winnable",
        })

    # ── 2. 5 OBD Clean Delivery Cases (OPEN_BOX → AUTO_CONTESTED) ─────────────
    for i in range(1, 6):
        disp_id = f"disp_obd_{i:03d}"
        pay_id = f"pay_obd_{i:03d}"
        ord_id = f"ord_obd_{i:03d}"
        amount = round(random.uniform(5000.0, 45000.0), 2)
        created_at = base_time + timedelta(hours=150 + i * 8)

        telemetry = {
            "otp": {"verified": True},
            "geofence": {"distance_km": round(random.uniform(0.02, 0.06), 3)},
            "weight": {"shipped_g": 800, "delivered_g": 798},
            "delivery_signature": True,
            "device_fingerprint_match": True,
            "defect_ticket_open": False,
            "delivery_type": "OPEN_BOX",
            "courier": "Blue Dart OBD",
        }

        cases.append({
            "dispute_id": disp_id, "payment_id": pay_id, "order_id": ord_id,
            "amount": amount, "reason_code": "product_not_received",
            "delivery_type": "OPEN_BOX",
            "telemetry": telemetry, "ocr_manifest": generate_mock_manifest("Blue Dart OBD", 798).model_dump_json(),
            "created_at": created_at, "category": "obd_clean",
        })

    # ── 3. 5 OBD Defective Merchandise (OBD + defective → AUTO_CONTESTED) ──────
    for i in range(1, 6):
        disp_id = f"disp_obd_def_{i:03d}"
        pay_id = f"pay_obd_def_{i:03d}"
        ord_id = f"ord_obd_def_{i:03d}"
        amount = round(random.uniform(8000.0, 35000.0), 2)
        created_at = base_time + timedelta(hours=190 + i * 6)

        telemetry = {
            "otp": {"verified": True},
            "geofence": {"distance_km": round(random.uniform(0.03, 0.07), 3)},
            "weight": {"shipped_g": 600, "delivered_g": 598},
            "delivery_signature": True,
            "device_fingerprint_match": True,
            "defect_ticket_open": False,
            "delivery_type": "OPEN_BOX",
            "courier": "Delhivery OBD",
        }

        cases.append({
            "dispute_id": disp_id, "payment_id": pay_id, "order_id": ord_id,
            "amount": amount, "reason_code": "defective_merchandise",
            "delivery_type": "OPEN_BOX",
            "telemetry": telemetry, "ocr_manifest": generate_mock_manifest("Delhivery OBD", 598).model_dump_json(),
            "created_at": created_at, "category": "obd_defective_override",
        })

    # ── 4. 5 Genuine Customer Defect / Loss Cases (Fairness Gate) ──────────────
    for i in range(1, 6):
        disp_id = f"disp_defect_{i:03d}"
        pay_id = f"pay_defect_{i:03d}"
        ord_id = f"ord_defect_{i:03d}"
        amount = round(random.uniform(2200.0, 18000.0), 2)
        courier = random.choice(COURIERS)
        created_at = base_time + timedelta(hours=220 + i * 8)

        if i <= 3:
            shipped_g, delivered_g = 800.0, 795.0
            telemetry = {
                "otp": {"verified": True}, "geofence": {"distance_km": 0.04},
                "weight": {"shipped_g": shipped_g, "delivered_g": delivered_g},
                "delivery_signature": True, "defect_ticket_open": True,
                "support_ticket": {"open": True, "ticket_id": f"TICK-{1000 + i}", "issue": "Item arrived broken"},
                "courier": courier, "delivery_type": "STANDARD",
            }
        else:
            shipped_g, delivered_g = 1200.0, 950.0  # 250g loss > 100g
            telemetry = {
                "otp": {"verified": True}, "geofence": {"distance_km": 0.05},
                "weight": {"shipped_g": shipped_g, "delivered_g": delivered_g},
                "delivery_signature": True, "defect_ticket_open": False,
                "courier": courier, "delivery_type": "STANDARD",
            }

        cases.append({
            "dispute_id": disp_id, "payment_id": pay_id, "order_id": ord_id,
            "amount": amount, "reason_code": "goods_damaged" if i <= 3 else "product_unacceptable",
            "delivery_type": "STANDARD",
            "telemetry": telemetry, "ocr_manifest": generate_mock_manifest(courier, delivered_g).model_dump_json(),
            "created_at": created_at, "category": "customer_defect_auto_accept",
        })

    # ── 5. 5 RAG Prior Complaint Cases (RAG fairness → AUTO_ACCEPTED) ──────────
    for i in range(1, 6):
        disp_id = f"disp_rag_{i:03d}"
        pay_id = f"pay_rag_{i:03d}"
        ord_id = f"ord_rag_{i:03d}"
        amount = round(random.uniform(3000.0, 25000.0), 2)
        created_at = base_time + timedelta(hours=260 + i * 6)

        telemetry = {
            "otp": {"verified": True}, "geofence": {"distance_km": 0.04},
            "weight": {"shipped_g": 500, "delivered_g": 498},
            "delivery_signature": True, "device_fingerprint_match": True,
            "defect_ticket_open": False, "delivery_type": "STANDARD",
            "courier": random.choice(COURIERS),
        }

        cases.append({
            "dispute_id": disp_id, "payment_id": pay_id, "order_id": ord_id,
            "amount": amount, "reason_code": "defective_merchandise",
            "delivery_type": "STANDARD",
            "telemetry": telemetry, "ocr_manifest": generate_mock_manifest("Delhivery", 498).model_dump_json(),
            "created_at": created_at, "category": "rag_prior_complaint",
        })

    # ── 6. 5 Ambiguous or High-Risk Cases ──────────────────────────────────────
    for i in range(1, 6):
        disp_id = f"disp_edge_{i:03d}"
        pay_id = f"pay_edge_{i:03d}"
        ord_id = f"ord_edge_{i:03d}"
        amount = round(random.uniform(900.0, 14000.0), 2)
        courier = random.choice(COURIERS)
        created_at = base_time + timedelta(hours=290 + i * 6)

        if i <= 3:
            # NEEDS_REVIEW — no OTP, moderate geofence
            telemetry = {
                "otp": {"verified": False},
                "geofence": {"distance_km": round(random.uniform(0.3, 0.8), 2)},
                "weight": {"shipped_g": 600, "delivered_g": 590},
                "delivery_signature": True, "device_fingerprint_match": False,
                "defect_ticket_open": False, "courier": courier, "delivery_type": "STANDARD",
            }
            reason = "product_not_received"
        else:
            # AUTO_ACCEPTED — very low score
            telemetry = {
                "otp": {"verified": False},
                "geofence": {"distance_km": round(random.uniform(25.0, 85.0), 1)},
                "weight": {"shipped_g": 600, "delivered_g": 0},
                "delivery_signature": False, "device_fingerprint_match": False,
                "defect_ticket_open": False, "courier": courier, "delivery_type": "STANDARD",
            }
            reason = "fraudulent_transaction"

        cases.append({
            "dispute_id": disp_id, "payment_id": pay_id, "order_id": ord_id,
            "amount": amount, "reason_code": reason,
            "delivery_type": "STANDARD",
            "telemetry": telemetry,
            "ocr_manifest": generate_mock_manifest(courier, 590.0 if i <= 3 else 0.0, i <= 3).model_dump_json(),
            "created_at": created_at, "category": "ambiguous_or_fraud",
        })

    return cases


def seed_database():
    """Populate SQLite database and ChromaDB with synthetic records."""
    logger.info("Initializing database tables...")
    init_db()

    # ── ChromaDB Seeding ───────────────────────────────────────────────────
    logger.info("Resetting and seeding ChromaDB collections...")
    client = get_chroma_client()
    reset_collections(client)

    policy_count = load_policy_documents(client)
    logger.info(f"  ✅ Loaded {policy_count} policy document chunks into ChromaDB")

    mock_chats = _generate_mock_chats()
    chat_count = load_customer_chats(client, mock_chats)
    logger.info(f"  ✅ Loaded {chat_count} omnichannel chat records into ChromaDB")

    # ── SQLite Seeding ────────────────────────────────────────────────────
    db = SessionLocal()
    try:
        db.query(Dispute).delete()
        db.commit()

        cases = generate_seed_cases()
        logger.info(f"Generating {len(cases)} synthetic dispute records...")

        from core.rag_engine import evaluate_rag_fairness_sync

        for c in cases:
            raw_json = json.dumps(c["telemetry"])
            delivery_type = c.get("delivery_type", "STANDARD")
            reason_code = c.get("reason_code", "product_not_received")

            # RAG fairness check
            rag_result = evaluate_rag_fairness_sync(
                dispute_id=c["dispute_id"],
                order_id=c["order_id"],
            )

            # Policy checklist
            policy = get_policy_checklist(reason_code=reason_code, delivery_type=delivery_type)
            policy_json = policy.model_dump_json()

            # Audit
            audit = evaluate_telemetry(
                raw_telemetry=raw_json,
                delivery_type=delivery_type,
                reason_code=reason_code,
                rag_fairness_triggered=rag_result.triggered,
                rag_fairness_summary=rag_result.summary,
                policy_checklist_json=policy_json,
            )

            evidence = compile_evidence(
                dispute_id=c["dispute_id"], payment_id=c["payment_id"],
                order_id=c["order_id"], amount=c["amount"],
                reason_code=reason_code, confidence_score=audit.confidence_score,
                raw_telemetry=raw_json, ocr_manifest_json=c["ocr_manifest"],
                delivery_type=delivery_type,
                rag_fairness_summary=rag_result.summary if rag_result.triggered else None,
                policy_checklist_json=policy_json,
                geofence_distance_m=audit.geofence_distance_m,
            )

            doc_id = f"doc_seed_{c['dispute_id'][-6:]}" if audit.decision == DisputeStatus.AUTO_CONTESTED else None

            dispute = Dispute(
                dispute_id=c["dispute_id"], payment_id=c["payment_id"],
                order_id=c["order_id"], status=audit.decision,
                reason_code=reason_code, amount=c["amount"],
                delivery_type=delivery_type,
                confidence_score=audit.confidence_score,
                otp_verified=audit.otp_verified,
                geofence_distance_km=audit.geofence_distance_km,
                geofence_distance_m=audit.geofence_distance_m,
                shipped_weight_g=audit.shipped_weight_g,
                delivered_weight_g=audit.delivered_weight_g,
                weight_loss_g=audit.weight_loss_g,
                defect_ticket_open=c["telemetry"].get("defect_ticket_open", False),
                fairness_gate_triggered=audit.fairness_gate_triggered,
                fairness_reason=audit.fairness_reason,
                rag_fairness_triggered=rag_result.triggered,
                rag_fairness_summary=rag_result.summary,
                policy_checklist_json=policy_json,
                evidence_text=evidence, document_id=doc_id,
                ocr_manifest_json=c["ocr_manifest"], raw_telemetry=raw_json,
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
