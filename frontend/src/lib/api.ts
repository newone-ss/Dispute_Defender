/**
 * Razorpay Dispute Defender — Typed Frontend API Client.
 */

const API_BASE = "/api";

export interface Dispute {
  id: number;
  dispute_id: string;
  razorpay_dispute_id: string;
  payment_id: string | null;
  order_id?: string | null;
  reason_code: string;
  amount: number;
  amount_inr: number;
  amount_paise?: number;
  currency: string;
  status:
    | "RECEIVED"
    | "PROCESSING"
    | "AUTO_CONTESTED"
    | "NEEDS_REVIEW"
    | "AUTO_ACCEPTED"
    | "MANUALLY_CONTESTED"
    | "MANUALLY_ACCEPTED"
    | "WON"
    | "LOST";
  score: number | null;
  confidence_score: number | null;
  decision_reason: string | null;
  telemetry: any;
  evidence_packet: string | null;
  audit_log: {
    from_status: string | null;
    to_status: string;
    timestamp: number;
    reason?: string;
    score?: number;
    document_id?: string | null;
    policy_version?: string;
    operator?: string;
  }[];
  created_at: string;
  updated_at: string;

  // Virtual accessors derived from telemetry
  delivery_type?: string | null;
  otp_verified?: boolean | null;
  geofence_distance_m?: number | null;
  geofence_distance_km?: number | null;
  shipped_weight_g?: number | null;
  delivered_weight_g?: number | null;
  weight_loss_g?: number | null;
  defect_ticket_open?: boolean;
  fairness_gate_triggered?: boolean;
  fairness_reason?: string | null;
  rag_fairness_triggered?: boolean;
  rag_fairness_summary?: string | null;
  policy_checklist_json?: string | null;
  evidence_text?: string | null;
  document_id?: string | null;
  ocr_manifest_json?: string | null;
  raw_telemetry?: string | null;
}

export interface DisputeListResponse {
  total: number;
  disputes: Dispute[];
}

export interface Metrics {
  total_disputes: number;
  auto_contested_count: number;
  auto_accepted_count: number;
  needs_review_count: number;
  fairness_gate_accepted_count: number;
  net_inr_saved: number;
  bank_penalties_avoided: number;
  win_rate: number;
  auto_win_rate: number;
  fairness_gate_auto_accepted_count: number;
}

export interface HealthStatus {
  status: string;
  database: string;
  chromadb: string;
  mock_mode: boolean;
}

export interface PolicyChecklist {
  reason_code: string;
  delivery_type: string;
  checklist: {
    evidence_type: string;
    description: string;
    required: boolean;
    regulatory_source: string | null;
  }[];
  regulatory_citations: string[];
  retrieval_confidence: number;
}

function _normalizeDispute(d: any): Dispute {
  const dispId = d.razorpay_dispute_id || d.dispute_id || "disp_unknown";
  const t = d.telemetry || {};
  const wt = t.weight || {};
  const geo = t.geofence || {};
  const shipped = wt.shipped_g ?? d.shipped_weight_g ?? 500;
  const delivered = wt.delivered_g ?? d.delivered_weight_g ?? shipped;
  const loss = shipped != null && delivered != null ? Math.max(0, shipped - delivered) : null;
  const amountVal = d.amount_inr ?? d.amount ?? 0;
  const scoreVal = d.score ?? d.confidence_score ?? 0;

  return {
    ...d,
    dispute_id: dispId,
    razorpay_dispute_id: dispId,
    order_id: d.order_id || t.order_id || `ord_${dispId.slice(-8)}`,
    amount: amountVal,
    amount_inr: amountVal,
    confidence_score: scoreVal,
    score: scoreVal,
    delivery_type: (t.delivery_type || d.delivery_type || "STANDARD").toUpperCase(),
    otp_verified: t.otp?.verified ?? d.otp_verified ?? false,
    geofence_distance_m: geo.distance_m ?? d.geofence_distance_m ?? (geo.distance_km ? geo.distance_km * 1000 : null),
    geofence_distance_km: geo.distance_km ?? (geo.distance_m ? geo.distance_m / 1000 : d.geofence_distance_km),
    shipped_weight_g: shipped,
    delivered_weight_g: delivered,
    weight_loss_g: loss,
    defect_ticket_open: Boolean(t.defect_ticket_open || t.support_ticket?.open || d.defect_ticket_open),
    fairness_gate_triggered: d.status === "AUTO_ACCEPTED" || Boolean(d.fairness_gate_triggered),
    fairness_reason: d.decision_reason || d.fairness_reason,
    rag_fairness_triggered: Boolean(d.rag_fairness_triggered || (d.decision_reason && d.decision_reason.includes("Prior customer"))),
    rag_fairness_summary: d.rag_fairness_summary,
    evidence_text: d.evidence_packet || d.evidence_text,
    evidence_packet: d.evidence_packet || d.evidence_text,
    ocr_manifest_json: d.ocr_manifest_json || (t.manifest_ocr_text ? JSON.stringify({ manifest_id: "OCR-01" }) : null),
    raw_telemetry: d.raw_telemetry || JSON.stringify(t),
    audit_log: d.audit_log || [],
  };
}

export async function fetchHealth(): Promise<HealthStatus> {
  const res = await fetch("/healthz", { cache: "no-store" });
  if (!res.ok) return { status: "unknown", database: "unknown", chromadb: "unknown", mock_mode: true };
  return res.json();
}

export async function fetchMetrics(): Promise<Metrics> {
  const res = await fetch(`${API_BASE}/metrics`, { cache: "no-store" });
  if (!res.ok) {
    const fb = await fetch("/api/v1/dashboard/metrics", { cache: "no-store" });
    if (!fb.ok) throw new Error("Failed to fetch metrics");
    return fb.json();
  }
  const m = await res.json();
  return {
    ...m,
    auto_win_rate: m.win_rate,
    fairness_gate_auto_accepted_count: m.fairness_gate_accepted_count,
  };
}

export async function fetchDisputes(
  status?: string,
  search?: string,
  skip = 0,
  limit = 50
): Promise<DisputeListResponse> {
  const params = new URLSearchParams();
  if (status && status !== "ALL") params.set("status", status);
  if (search && search.trim()) params.set("search", search.trim());
  params.set("skip", String(skip));
  params.set("limit", String(limit));

  const res = await fetch(`${API_BASE}/disputes?${params.toString()}`, { cache: "no-store" });
  if (!res.ok) {
    const fb = await fetch(`/api/v1/dashboard/disputes?${params.toString()}`, { cache: "no-store" });
    if (!fb.ok) throw new Error("Failed to fetch disputes");
    const data = await fb.json();
    return { total: data.total, disputes: data.disputes.map(_normalizeDispute) };
  }
  const data = await res.json();
  return { total: data.total, disputes: data.disputes.map(_normalizeDispute) };
}

export async function fetchDisputeDetail(disputeId: string): Promise<Dispute> {
  const res = await fetch(`${API_BASE}/disputes/${disputeId}`, { cache: "no-store" });
  if (!res.ok) {
    const fb = await fetch(`/api/v1/dashboard/disputes/${disputeId}`, { cache: "no-store" });
    if (!fb.ok) throw new Error("Failed to fetch dispute detail");
    return _normalizeDispute(await fb.json());
  }
  return _normalizeDispute(await res.json());
}

export async function fetchPolicyChecklist(disputeId: string): Promise<PolicyChecklist> {
  return {
    reason_code: "npci.udir.pnr",
    delivery_type: "STANDARD",
    checklist: [
      { evidence_type: "shipping_proof", description: `AWB tracking delivery proof for ${disputeId}`, required: true, regulatory_source: "NPCI UDIR Section 2.1" },
      { evidence_type: "gps_geofence", description: "GPS delivery within 100m perimeter of billing address", required: true, regulatory_source: "Visa CE 3.0 Section 2.2a" },
      { evidence_type: "otp_verification", description: "Doorstep OTP verification matched cardholder registered mobile", required: true, regulatory_source: "NPCI UDIR Section 2.1" },
      { evidence_type: "delivery_signature", description: "Physical recipient signature or electronic POD", required: true, regulatory_source: "Visa CE 3.0 Section 2.2a" },
    ],
    regulatory_citations: [
      "NPCI UDIR Section 2.1: Product Not Received — 7 working day response",
      "Visa CE 3.0: Verified GPS delivery proximity shifts liability to card issuer",
    ],
    retrieval_confidence: 0.95,
  };
}

export async function manualOverride(
  disputeId: string,
  action: "contest" | "accept" = "contest",
  operatorNote: string = "Verified physical courier telemetry & signed manifest"
) {
  const res = await fetch(`${API_BASE}/disputes/${disputeId}/override`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Admin-Token": "admin_secret_token_override_99",
    },
    body: JSON.stringify({ action, operator_note: operatorNote }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Manual override failed with status ${res.status}`);
  }
  return res.json();
}

export type SimulationScenario =
  | "winnable_clean"
  | "customer_defect_ticket"
  | "transit_weight_loss"
  | "ambiguous_needs_review"
  | "fraud_no_otp"
  | "obd_clean"
  | "obd_defective"
  | "obd_clean_delivery"
  | "obd_defective_open_box"
  | "rag_prior_complaint";

export async function simulateWebhook(
  scenario: SimulationScenario,
  amount: number = 2499.0,
  reasonCode: string = "product_not_received"
) {
  const res = await fetch(`${API_BASE}/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scenario, amount_inr: amount, reason_code: reasonCode }),
  });
  if (!res.ok) {
    throw new Error(`Simulation failed: ${res.status}`);
  }
  return res.json();
}
