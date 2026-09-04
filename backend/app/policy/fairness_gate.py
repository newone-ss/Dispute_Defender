"""Pure Consumer Fairness Gate and master Decision Router.

Protects consumers by automatically accepting disputes on genuine defects or transit loss,
releasing merchant liability and avoiding the ₹1,500 bank dispute penalty.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

from app.core.models import DisputeStatus
from app.core.schemas import ChatHit, GateResult, ScoreBreakdown, TelemetryData
from app.policy.reason_codes import ReasonCodeEntry


@lru_cache(maxsize=1)
def load_scoring_policy(policy_path: str) -> Dict[str, Any]:
    """Load and cache the declarative scoring policy YAML definition."""
    p = Path(policy_path)
    if not p.is_file():
        # Fallback to relative parent if running from root
        p = Path(__file__).resolve().parent / "scoring_policy.yaml"
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def fairness_gate(
    telemetry: TelemetryData,
    support_tickets: List[ChatHit],
    policy: Dict[str, Any],
) -> GateResult:
    """Pure evaluation of Consumer Fairness Gates without I/O."""
    weight_cfg = policy.get("weight", {})
    loss_threshold = weight_cfg.get("fairness_weight_loss_g", 100.0)

    # 1. Check open defect support ticket in CRM
    if telemetry.defect_ticket_open:
        return GateResult(
            triggered=True,
            action="AUTO_ACCEPT",
            reason="Consumer Fairness: Open merchant defect ticket active prior to chargeback",
        )

    # 2. Check transit weight loss indicating empty box or missing parts
    shipped = telemetry.shipped_weight_g
    delivered = telemetry.delivered_weight_g
    if shipped is not None and delivered is not None:
        loss_g = max(0.0, shipped - delivered)
        if loss_g > loss_threshold:
            return GateResult(
                triggered=True,
                action="AUTO_ACCEPT",
                reason=f"Consumer Fairness: Transit weight loss of {loss_g:.1f}g exceeded {loss_threshold}g limit",
            )

    # 3. Check prior omnichannel chat complaints retrieved via RAG
    for hit in support_tickets:
        if hit.score >= 0.70:
            return GateResult(
                triggered=True,
                action="AUTO_ACCEPT",
                reason=f"Consumer Fairness: Prior customer communication verified via {hit.source}: '{hit.text[:80]}...'",
            )

    return GateResult(triggered=False, action="PASS_THROUGH", reason=None)


def resolve_decision(
    score_breakdown: ScoreBreakdown,
    gate_result: GateResult,
    reason_entry: ReasonCodeEntry,
    delivery_type: str = "STANDARD",
    is_unmapped: bool = False,
    policy: Dict[str, Any] = None,
) -> Tuple[DisputeStatus, str]:
    """Master decision router combining score, fairness gate, reason codes, and delivery type."""
    policy = policy or {}
    thresholds = policy.get("thresholds", {})
    auto_min = thresholds.get("auto_contest_min_score", 80)
    review_min = thresholds.get("needs_review_min_score", 40)

    # Priority 1: Unmapped reason code -> Always route to human review
    if is_unmapped:
        return (
            DisputeStatus.NEEDS_REVIEW,
            "Unmapped reason code requires human risk operator classification",
        )

    # Priority 2: Consumer Fairness Gate -> Immediate auto-accept to save ₹1,500 penalty
    if gate_result.triggered:
        return DisputeStatus.AUTO_ACCEPTED, gate_result.reason or "Consumer Fairness Gate triggered"

    # Priority 3: Defective claim on Standard delivery -> OTP/GPS does not prove integrity
    dt_upper = delivery_type.upper()
    if reason_entry.requires_open_box_inspection and dt_upper != "OPEN_BOX":
        return (
            DisputeStatus.NEEDS_REVIEW,
            "Defective claim on standard delivery: physical contents require manual review",
        )

    # Priority 4: Defective claim with verified Open Box Delivery (OBD)
    if reason_entry.requires_open_box_inspection and dt_upper == "OPEN_BOX":
        if score_breakdown.otp_points > 0:
            return (
                DisputeStatus.AUTO_CONTESTED,
                "Open Box Delivery (OBD) verified: cardholder physically inspected item at doorstep before entering OTP",
            )
        else:
            return (
                DisputeStatus.NEEDS_REVIEW,
                "Open Box Delivery attempted but doorstep OTP inspection was unverified",
            )

    # Priority 5: Threshold-based scoring cutoffs
    if score_breakdown.total_score >= auto_min:
        return (
            DisputeStatus.AUTO_CONTESTED,
            f"Conclusive courier telemetry score ({score_breakdown.total_score}/100) exceeds threshold ({auto_min})",
        )
    elif score_breakdown.total_score >= review_min:
        return (
            DisputeStatus.NEEDS_REVIEW,
            f"Ambiguous courier telemetry score ({score_breakdown.total_score}/100) routed to review queue",
        )
    else:
        return (
            DisputeStatus.AUTO_ACCEPTED,
            f"Insufficient courier evidence score ({score_breakdown.total_score}/100) auto-accepted to release liability",
        )
