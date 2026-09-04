"""Seed script populating SQLite disputes and ChromaDB customer chat transcripts."""

import random
import time

from app.core.database import SessionLocal, init_db
from app.core.doc_loader import get_chroma_client, load_customer_chats, load_policy_documents
from app.core.models import Dispute, DisputeStatus


def seed():
    """Seed SQLite database and ChromaDB collections with synthetic scenarios."""
    from app.core.database import Base, engine

    print("[*] Recreating database schema...")
    Base.metadata.drop_all(bind=engine)
    init_db()

    db = SessionLocal()
    client = get_chroma_client()

    print("[*] Loading policy documents into ChromaDB...")
    load_policy_documents(client, force_reindex=True)

    print("[*] Clearing existing dispute records...")
    db.query(Dispute).delete()
    db.commit()

    print("[*] Generating 50 realistic test disputes...")
    sample_chats = []

    for i in range(1, 51):
        disp_id = f"disp_seed_{i:04d}"
        pay_id = f"pay_seed_{i:04d}"
        amount = random.choice([999.0, 1499.0, 2499.0, 4999.0, 12999.0])
        reason = random.choice(["product_not_received", "defective_merchandise", "13.1", "10.4"])
        dt = "OPEN_BOX" if i % 4 == 0 else "STANDARD"

        # Scenario distribution: 30 winnable, 10 fairness defect, 10 ambiguous
        if i <= 30:
            st = DisputeStatus.AUTO_CONTESTED
            score = random.randint(85, 98)
            reason_str = "Conclusive courier telemetry: OTP verified & delivery within 50m"
            telemetry = {
                "otp": {"verified": True},
                "geofence": {"distance_m": round(random.uniform(20.0, 75.0), 1)},
                "weight": {"shipped_g": 520, "delivered_g": 518},
                "delivery_signature": True,
                "device": {"fingerprint_match": True},
                "delivery_type": dt,
            }
        elif i <= 40:
            st = DisputeStatus.AUTO_ACCEPTED
            score = random.randint(20, 38)
            reason_str = "Consumer Fairness Gate: Transit weight loss > 100g on delivery"
            telemetry = {
                "otp": {"verified": True},
                "geofence": {"distance_m": 45.0},
                "weight": {"shipped_g": 850, "delivered_g": 510},
                "defect_ticket_open": i % 2 == 0,
                "delivery_signature": True,
                "delivery_type": dt,
            }
            sample_chats.append(
                {
                    "dispute_id": disp_id,
                    "channel": "whatsapp",
                    "message": "Hi, I received the box today but it was completely damaged and empty inside! Please refund.",
                    "timestamp": "2026-09-02 10:15:00",
                }
            )
        else:
            st = DisputeStatus.NEEDS_REVIEW
            score = random.randint(45, 75)
            reason_str = "Ambiguous courier telemetry: unverified OTP or geofence boundary offset"
            telemetry = {
                "otp": {"verified": False},
                "geofence": {"distance_m": round(random.uniform(350.0, 750.0), 1)},
                "weight": {"shipped_g": 500, "delivered_g": 485},
                "delivery_signature": True,
                "delivery_type": dt,
            }

        dispute = Dispute(
            razorpay_dispute_id=disp_id,
            payment_id=pay_id,
            idempotency_key=f"{disp_id}:{int(time.time())}",
            reason_code=reason,
            amount_paise=int(amount * 100),
            currency="INR",
            status=st,
            score=score,
            decision_reason=reason_str,
            telemetry=telemetry,
            evidence_packet=f"# Evidence Packet for {disp_id}\n- Telemetry Score: {score}/100\n- Status: {st.value}\n",
            audit_log=[
                {
                    "from_status": None,
                    "to_status": DisputeStatus.RECEIVED.value,
                    "timestamp": time.time(),
                },
                {
                    "from_status": DisputeStatus.RECEIVED.value,
                    "to_status": st.value,
                    "timestamp": time.time(),
                    "reason": reason_str,
                },
            ],
        )
        db.add(dispute)

    db.commit()
    db.close()

    print(f"[*] Indexing {len(sample_chats)} customer support chat records into ChromaDB...")
    load_customer_chats(client, sample_chats, force_reindex=True)
    print("[OK] Seed completed successfully: 50 disputes and ChromaDB collections ready.")


if __name__ == "__main__":
    seed()
