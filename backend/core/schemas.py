"""Pydantic schemas for API validation, serialization, and telemetry payloads."""

from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List
from datetime import datetime
from core.models import DisputeStatus


# ── Webhook Schemas ─────────────────────────────────────────────────────────

class WebhookPayload(BaseModel):
    """Permissive webhook payload parser for incoming Razorpay events."""
    event: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None

    model_config = {"extra": "allow"}


# ── OCR Manifest Schemas ───────────────────────────────────────────────────

class ManifestData(BaseModel):
    """Typed extraction of an unstructured courier delivery manifest."""
    manifest_id: Optional[str] = None
    courier_partner: Optional[str] = "Delhivery"
    awb_number: Optional[str] = None
    recipient_name: Optional[str] = None
    delivery_timestamp: Optional[str] = None
    signature_present: bool = False
    measured_weight_g: Optional[float] = None
    ocr_confidence_score: float = Field(default=0.95, ge=0.0, le=1.0)
    raw_extracted_text: Optional[str] = None


# ── Audit Engine Schemas ───────────────────────────────────────────────────

class AuditBreakdown(BaseModel):
    """Detailed audit scores and fairness triggers."""
    confidence_score: float
    decision: DisputeStatus
    otp_verified: bool
    otp_points: float
    geofence_distance_km: Optional[float] = None
    geofence_points: float
    shipped_weight_g: Optional[float] = None
    delivered_weight_g: Optional[float] = None
    weight_loss_g: Optional[float] = None
    weight_points: float
    delivery_signature: bool
    signature_points: float
    device_fingerprint_match: bool
    device_points: float
    fairness_gate_triggered: bool
    fairness_reason: Optional[str] = None


# ── Dispute API Schemas ─────────────────────────────────────────────────────

class DisputeOut(BaseModel):
    """Serialized dispute model for the frontend table and detail view."""
    id: int
    dispute_id: str
    payment_id: Optional[str] = None
    order_id: Optional[str] = None
    status: DisputeStatus
    reason_code: Optional[str] = None
    amount: float
    confidence_score: Optional[float] = None
    otp_verified: Optional[bool] = None
    geofence_distance_km: Optional[float] = None
    shipped_weight_g: Optional[float] = None
    delivered_weight_g: Optional[float] = None
    weight_loss_g: Optional[float] = None
    defect_ticket_open: bool = False
    fairness_gate_triggered: bool = False
    fairness_reason: Optional[str] = None
    evidence_text: Optional[str] = None
    document_id: Optional[str] = None
    ocr_manifest_json: Optional[str] = None
    raw_telemetry: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DisputeListOut(BaseModel):
    """Paginated dispute list response."""
    total: int
    disputes: List[DisputeOut]


class MetricsOut(BaseModel):
    """Financial and operational metrics for the merchant dashboard."""
    total_disputes: int = 0
    net_inr_saved: float = 0.0              # Contested revenue protected + won
    bank_penalties_avoided: float = 0.0     # Auto-accepted cases * ₹1,500
    auto_win_rate: float = 0.0              # Estimated or calculated auto win %
    needs_review_count: int = 0
    auto_contested_count: int = 0
    auto_accepted_count: int = 0
    fairness_gate_auto_accepted_count: int = 0


class ManualOverrideRequest(BaseModel):
    """Payload to trigger human-in-the-loop manual contest submission."""
    dispute_id: str
    notes: Optional[str] = None


class ManualOverrideResponse(BaseModel):
    """Response returned upon manual contest submission."""
    dispute_id: str
    new_status: DisputeStatus
    document_id: Optional[str] = None
    message: str


class SimulateWebhookRequest(BaseModel):
    """Request payload to simulate a realistic Razorpay dispute webhook."""
    scenario: str = Field(
        default="winnable_clean",
        description="Scenario: 'winnable_clean', 'customer_defect_ticket', 'transit_weight_loss', 'ambiguous_needs_review', or 'fraud_no_otp'",
    )
    amount: Optional[float] = 3499.0
    reason_code: Optional[str] = "product_not_received"
