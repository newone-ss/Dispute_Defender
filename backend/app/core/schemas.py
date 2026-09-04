"""Pydantic v2 schemas defining internal contracts and external API surfaces."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.core.models import DisputeStatus


class WebhookResponse(BaseModel):
    """Immediate, typed response returned by the sub-25ms webhook ingestion handler."""

    status: str = Field(..., description="Ingestion status (received | duplicate | ignored)")
    dispute_id: str
    decision: str = Field(..., description="Action taken: inserted | duplicate")
    latency_ms: float


class TelemetryData(BaseModel):
    """Normalized courier physical delivery signals."""

    delivery_type: str = "STANDARD"  # STANDARD | OPEN_BOX | LOCKER
    otp_verified: bool = False
    geofence_distance_m: Optional[float] = None
    geofence_distance_km: Optional[float] = None
    shipped_weight_g: Optional[float] = None
    delivered_weight_g: Optional[float] = None
    delivery_signature: bool = False
    device_fingerprint_match: bool = False
    defect_ticket_open: bool = False
    raw_ocr_text: Optional[str] = None
    courier: Optional[str] = None
    awb_number: Optional[str] = None


class ScoreBreakdown(BaseModel):
    """Individual signal point breakdown from the pure scoring engine."""

    total_score: int = Field(..., ge=0, le=100)
    otp_points: float
    geofence_points: float
    weight_points: float
    signature_points: float
    device_points: float
    geofence_distance_m: Optional[float] = None
    weight_loss_g: float = 0.0


class GateResult(BaseModel):
    """Outcome of the Consumer Fairness Gate evaluation."""

    triggered: bool
    reason: Optional[str] = None
    action: str = Field("PASS_THROUGH", description="AUTO_ACCEPT | PASS_THROUGH")


class ChatHit(BaseModel):
    """Omnichannel support transcript search hit from ChromaDB."""

    source: str
    text: str
    score: float
    timestamp: Optional[str] = None


class PolicyCitation(BaseModel):
    """Regulatory passage retrieved from NPCI or Visa rulebooks."""

    network: str
    clause_id: str
    text: str
    source_file: str
    policy_version: str


class ManifestData(BaseModel):
    """Typed courier delivery manifest parsed from scanned text."""

    manifest_id: str
    courier_partner: str
    awb_number: str
    recipient_name: str
    delivery_timestamp: Optional[str] = None
    signature_present: bool
    measured_weight_g: float
    ocr_confidence_score: float
    raw_extracted_text: str = ""


class DisputeOut(BaseModel):
    """Public dispute schema for dashboard representation."""

    id: int
    razorpay_dispute_id: str
    payment_id: Optional[str]
    reason_code: str
    amount_inr: float
    amount_paise: int
    currency: str
    status: DisputeStatus
    score: Optional[int]
    decision_reason: Optional[str]
    telemetry: Optional[Dict[str, Any]]
    evidence_packet: Optional[str]
    audit_log: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class DisputeListOut(BaseModel):
    """Paginated list of disputes."""

    total: int
    disputes: List[DisputeOut]


class MetricsOut(BaseModel):
    """Aggregated financial ROI and dispute counts."""

    total_disputes: int
    auto_contested_count: int
    auto_accepted_count: int
    needs_review_count: int
    fairness_gate_accepted_count: int
    net_inr_saved: float
    bank_penalties_avoided: float
    win_rate: float


class ManualOverrideRequest(BaseModel):
    """Payload for operator manual review override."""

    action: str = Field(..., pattern="^(contest|accept)$")
    operator_note: str = Field(..., min_length=3, description="Mandatory audit trail note")


class ManualOverrideResponse(BaseModel):
    """Result of an authenticated manual dispute override."""

    dispute_id: str
    new_status: DisputeStatus
    message: str


class SimulateRequest(BaseModel):
    """Request schema for triggering simulated chargeback webhooks."""

    scenario: str = Field(
        ...,
        description="winnable_clean | customer_defect_ticket | transit_weight_loss | ambiguous_needs_review | obd_clean | obd_defective | fraud_no_otp",
    )
    amount_inr: float = 2499.0
    reason_code: str = "product_not_received"


class DocumentRef(BaseModel):
    """Receipt returned after evidence upload to Razorpay Documents API."""

    id: str
    entity: str = "document"
    name: str
    mock: bool = False


class ContestAck(BaseModel):
    """Acknowledgment of contest submission from Razorpay Disputes API."""

    dispute_id: str
    status: str
    action: str = "submit"
    document_ids: List[str] = Field(default_factory=list)
    mock: bool = False


class AcceptAck(BaseModel):
    """Acknowledgment of dispute liability acceptance from Razorpay Disputes API."""

    dispute_id: str
    status: str = "accepted"
    mock: bool = False
