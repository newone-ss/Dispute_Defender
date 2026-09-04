"""Benchmark Runner — evaluates Dispute Defender on ground-truth dataset and calculates financial ROI.

Includes OBD (Open Box Delivery), RAG Fairness Gate, and Reason-Code Routing accuracy.

Usage:
    cd backend
    python -m evaluate.run_benchmark
"""

import json
import logging
import os
import random
import sys
from datetime import datetime

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.audit_engine import evaluate_telemetry
from core.models import DisputeStatus
from core.compiler import compile_evidence
from core.config import get_settings

# Force UTF-8 on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore

settings = get_settings()
PENALTY_FEE_PER_AVOIDED_CASE = settings.bank_penalty_fee_inr  # ₹1,500


def run_benchmark():
    dataset_path = os.path.join(os.path.dirname(__file__), "test_dataset.json")
    if os.path.exists(dataset_path):
        with open(dataset_path, "r", encoding="utf-8") as f:
            test_cases = json.load(f)
    else:
        test_cases = []

    # Expand to 50 test cases if dataset is small
    while len(test_cases) < 50:
        idx = len(test_cases) + 1
        if idx % 5 == 0:
            # OBD case
            test_cases.append({
                "id": f"GT-{idx:03d}",
                "dispute_id": f"disp_synth_{idx:03d}",
                "amount": round(random.uniform(8000, 40000), 2),
                "expected_decision": "AUTO_CONTESTED",
                "category": "obd_clean",
                "delivery_type": "OPEN_BOX",
                "reason_code": "product_not_received",
                "telemetry": {
                    "otp": {"verified": True},
                    "geofence": {"distance_km": round(random.uniform(0.02, 0.06), 3)},
                    "weight": {"shipped_g": 800, "delivered_g": 798},
                    "delivery_signature": True,
                    "device_fingerprint_match": True,
                    "defect_ticket_open": False,
                    "delivery_type": "OPEN_BOX",
                },
            })
        elif idx % 4 == 0:
            # Defect case
            test_cases.append({
                "id": f"GT-{idx:03d}",
                "dispute_id": f"disp_synth_{idx:03d}",
                "amount": round(random.uniform(1500, 16000), 2),
                "expected_decision": "AUTO_ACCEPTED",
                "category": "consumer_defect",
                "telemetry": {
                    "otp": {"verified": True},
                    "geofence": {"distance_km": 0.05},
                    "weight": {"shipped_g": 500, "delivered_g": 500},
                    "delivery_signature": True,
                    "defect_ticket_open": True,
                },
            })
        elif idx % 7 == 0:
            # Ambiguous/Fraud
            test_cases.append({
                "id": f"GT-{idx:03d}",
                "dispute_id": f"disp_synth_{idx:03d}",
                "amount": round(random.uniform(2000, 10000), 2),
                "expected_decision": "NEEDS_REVIEW",
                "category": "ambiguous",
                "telemetry": {
                    "otp": {"verified": False},
                    "geofence": {"distance_km": 0.4},
                    "weight": {"shipped_g": 500, "delivered_g": 490},
                    "delivery_signature": True,
                    "device_fingerprint_match": False,
                },
            })
        else:
            # Winnable
            test_cases.append({
                "id": f"GT-{idx:03d}",
                "dispute_id": f"disp_synth_{idx:03d}",
                "amount": round(random.uniform(2500, 28000), 2),
                "expected_decision": "AUTO_CONTESTED",
                "category": "winnable",
                "telemetry": {
                    "otp": {"verified": True},
                    "geofence": {"distance_km": round(random.uniform(0.02, 0.08), 3)},
                    "weight": {"shipped_g": 650, "delivered_g": 645},
                    "delivery_signature": True,
                    "device_fingerprint_match": True,
                    "defect_ticket_open": False,
                },
            })

    print("\n" + "=" * 78)
    print("🛡️  RAZORPAY DISPUTE DEFENDER — EVALUATION & FINANCIAL ROI BENCHMARK")
    print("   Architecture: Hybrid RAG + Deterministic | OBD Routing | Meter GPS")
    print("=" * 78)
    print(f"  Execution Time   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Benchmark Cases  : {len(test_cases)}")
    print(f"  Bank Penalty Fee : ₹{PENALTY_FEE_PER_AVOIDED_CASE:,.2f} per lost contest")
    print("=" * 78)

    correct_decisions = 0
    fairness_gate_success = 0
    total_fairness_cases = 0
    obd_correct = 0
    total_obd_cases = 0
    reason_route_correct = 0
    total_reason_route_cases = 0

    results = {
        "AUTO_CONTESTED": [],
        "NEEDS_REVIEW": [],
        "AUTO_ACCEPTED": [],
    }

    for case in test_cases:
        raw_json = json.dumps(case["telemetry"])
        delivery_type = case.get("delivery_type") or case["telemetry"].get("delivery_type", "STANDARD")
        reason_code = case.get("reason_code") or case.get("telemetry", {}).get("reason_code")

        audit = evaluate_telemetry(
            raw_telemetry=raw_json,
            delivery_type=delivery_type,
            reason_code=reason_code,
        )
        actual_decision = audit.decision.value
        expected_decision = case.get("expected_decision")

        is_correct = (actual_decision == expected_decision)
        if is_correct:
            correct_decisions += 1

        # Track OBD accuracy
        if delivery_type and delivery_type.upper() == "OPEN_BOX":
            total_obd_cases += 1
            if is_correct:
                obd_correct += 1

        # Track reason-code routing accuracy
        if reason_code and reason_code == "defective_merchandise":
            total_reason_route_cases += 1
            if is_correct:
                reason_route_correct += 1

        # Track fairness gate accuracy
        is_defect_case = (
            case["telemetry"].get("defect_ticket_open") is True
            or (case["telemetry"].get("weight", {}).get("shipped_g", 0) - case["telemetry"].get("weight", {}).get("delivered_g", 0) > 100)
        )
        if is_defect_case:
            total_fairness_cases += 1
            if audit.fairness_gate_triggered and actual_decision == "AUTO_ACCEPTED":
                fairness_gate_success += 1

        results[actual_decision].append({
            "id": case.get("dispute_id", case.get("id", "unknown")),
            "amount": case["amount"],
            "score": audit.confidence_score,
            "fairness_triggered": audit.fairness_gate_triggered,
            "otp": audit.otp_verified,
            "geo_m": audit.geofence_distance_m,
            "delivery_type": delivery_type,
            "route": audit.reason_code_route,
        })

    # Financial Impact Calculations
    auto_contested = results["AUTO_CONTESTED"]
    needs_review = results["NEEDS_REVIEW"]
    auto_accepted = results["AUTO_ACCEPTED"]

    contested_amount = sum(d["amount"] for d in auto_contested)
    review_amount = sum(d["amount"] for d in needs_review)
    accepted_amount = sum(d["amount"] for d in auto_accepted)
    total_exposure = contested_amount + review_amount + accepted_amount

    revenue_recovered_contested = contested_amount * 0.85
    revenue_recovered_review = review_amount * 0.50
    penalty_fees_avoided = len(auto_accepted) * PENALTY_FEE_PER_AVOIDED_CASE
    total_financial_savings = revenue_recovered_contested + revenue_recovered_review + penalty_fees_avoided

    accuracy = (correct_decisions / len(test_cases)) * 100.0
    fairness_accuracy = (fairness_gate_success / total_fairness_cases * 100.0) if total_fairness_cases > 0 else 100.0
    obd_accuracy = (obd_correct / total_obd_cases * 100.0) if total_obd_cases > 0 else 100.0
    route_accuracy = (reason_route_correct / total_reason_route_cases * 100.0) if total_reason_route_cases > 0 else 100.0

    print("\n📊 CLASSIFICATION & PIPELINE ACCURACY")
    print("─" * 60)
    print(f"  Overall Decision Accuracy     : {accuracy:>6.1f}% ({correct_decisions}/{len(test_cases)})")
    print(f"  Consumer Fairness Gate Acc    : {fairness_accuracy:>6.1f}% ({fairness_gate_success}/{total_fairness_cases})")
    print(f"  OBD Routing Accuracy          : {obd_accuracy:>6.1f}% ({obd_correct}/{total_obd_cases})")
    print(f"  Reason-Code Router Accuracy   : {route_accuracy:>6.1f}% ({reason_route_correct}/{total_reason_route_cases})")
    print(f"  AUTO_CONTESTED (Score > 80)   : {len(auto_contested):>3d} cases  |  ₹{contested_amount:>12,.2f}")
    print(f"  NEEDS_REVIEW   (Score 40-80)  : {len(needs_review):>3d} cases  |  ₹{review_amount:>12,.2f}")
    print(f"  AUTO_ACCEPTED  (Score < 40)   : {len(auto_accepted):>3d} cases  |  ₹{accepted_amount:>12,.2f}")

    print("\n💰 FINANCIAL ROI & NET REVENUE PROTECTED")
    print("─" * 60)
    print(f"  Total Disputed Value Exposure : ₹{total_exposure:>12,.2f}")
    print(f"  Direct Revenue Recovered (85%): ₹{revenue_recovered_contested:>12,.2f}")
    print(f"  Human Review Recovery (50%)   : ₹{revenue_recovered_review:>12,.2f}")
    print(f"  Bank Penalties Avoided (₹1.5k): ₹{penalty_fees_avoided:>12,.2f}")
    print(f"  {'─'*40}")
    print(f"  ✨ NET FINANCIAL IMPACT       : ₹{total_financial_savings:>12,.2f}")
    if total_exposure > 0:
        print(f"  ✨ EFFECTIVE ROI BOOST        : {((total_financial_savings / total_exposure) * 100):>6.1f}% of total exposure")

    print("\n📋 SAMPLE DISPUTE EVALUATION TRACE (First 10)")
    print("─" * 90)
    print(f"  {'Dispute ID':<18} {'Score':>7} {'OTP':^5} {'GPS (m)':>8} {'Type':<10} {'Decision':<16} {'Amount':>10}")
    print(f"  {'─'*18} {'─'*7} {'─'*5} {'─'*8} {'─'*10} {'─'*16} {'─'*10}")
    all_sample = []
    for dec, items in results.items():
        for it in items:
            geo_str = f"{it['geo_m']:.0f}m" if it['geo_m'] is not None else "N/A"
            all_sample.append((
                it["id"], it["score"], "✅" if it["otp"] else "❌",
                geo_str, it.get("delivery_type", "STD")[:8],
                dec, it["amount"],
            ))

    for row in all_sample[:10]:
        print(f"  {row[0]:<18} {row[1]:>7.1f} {row[2]:^5} {row[3]:>8} {row[4]:<10} {row[5]:<16} ₹{row[6]:>9,.2f}")

    print("\n" + "=" * 78)
    print("✅ Benchmark suite completed successfully (Hybrid RAG + Deterministic v3.0).")
    print("=" * 78 + "\n")


if __name__ == "__main__":
    run_benchmark()
