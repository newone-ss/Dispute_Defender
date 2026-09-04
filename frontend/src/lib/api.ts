/**
 * Razorpay Dispute Defender — Frontend API Client.
 *
 * Interacts with FastAPI backend endpoints:
 * - /api/v1/dashboard/metrics
 * - /api/v1/dashboard/disputes
 * - /api/v1/dashboard/disputes/:id
 * - /api/v1/dashboard/disputes/:id/override
 * - /api/v1/dashboard/disputes/:id/policy-checklist
 * - /api/v1/dashboard/simulate
 */

const API_BASE = "/api/v1/dashboard";

export interface Dispute {
  id: number;
  dispute_id: string;
  payment_id: string | null;
  order_id: string | null;
  status: "RECEIVED" | "PROCESSING" | "AUTO_CONTESTED" | "NEEDS_REVIEW" | "AUTO_ACCEPTED" | "MANUALLY_CONTESTED" | "WON" | "LOST";
  reason_code: string | null;
  amount: number;
  confidence_score: number | null;

  // Delivery type (OBD)
  delivery_type: string | null;

  // Telemetry
  otp_verified: boolean | null;
  geofence_distance_km: number | null;
  geofence_distance_m: number | null;
  shipped_weight_g: number | null;
  delivered_weight_g: number | null;
  weight_loss_g: number | null;
  defect_ticket_open: boolean;
  fairness_gate_triggered: boolean;
  fairness_reason: string | null;

  // RAG fairness gate
  rag_fairness_triggered: boolean;
  rag_fairness_summary: string | null;

  // Policy RAG
  policy_checklist_json: string | null;

  // Evidence & OCR
  evidence_text: string | null;
  document_id: string | null;
  ocr_manifest_json: string | null;
  raw_telemetry: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface DisputeListResponse {
  total: number;
  disputes: Dispute[];
}

export interface Metrics {
  total_disputes: number;
  net_inr_saved: number;
  bank_penalties_avoided: number;
  auto_win_rate: number;
  needs_review_count: number;
  auto_contested_count: number;
  auto_accepted_count: number;
  fairness_gate_auto_accepted_count: number;
}

export interface ManualOverrideResponse {
  dispute_id: string;
  new_status: string;
  document_id: string | null;
  message: string;
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

export async function fetchMetrics(): Promise<Metrics> {
  const res = await fetch(`${API_BASE}/metrics`, { cache: "no-store" });
  if (!res.ok) {
    const fallbackRes = await fetch("/disputes/metrics", { cache: "no-store" });
    if (!fallbackRes.ok) throw new Error(`Failed to fetch metrics: ${res.status}`);
    return fallbackRes.json();
  }
  return res.json();
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

  const res = await fetch(`${API_BASE}/disputes?${params.toString()}`, {
    cache: "no-store",
  });
  if (!res.ok) {
    const fallback = await fetch(`/disputes?${params.toString()}`, { cache: "no-store" });
    if (!fallback.ok) throw new Error(`Failed to fetch disputes: ${res.status}`);
    return fallback.json();
  }
  return res.json();
}

export async function fetchDisputeDetail(disputeId: string): Promise<Dispute> {
  const res = await fetch(`${API_BASE}/disputes/${disputeId}`, { cache: "no-store" });
  if (!res.ok) {
    const fallback = await fetch(`/disputes/${disputeId}`, { cache: "no-store" });
    if (!fallback.ok) throw new Error(`Failed to fetch dispute detail: ${res.status}`);
    return fallback.json();
  }
  return res.json();
}

export async function fetchPolicyChecklist(disputeId: string): Promise<PolicyChecklist> {
  const res = await fetch(`${API_BASE}/disputes/${disputeId}/policy-checklist`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch policy checklist: ${res.status}`);
  return res.json();
}

export async function manualOverride(disputeId: string): Promise<ManualOverrideResponse> {
  const res = await fetch(`${API_BASE}/disputes/${disputeId}/override`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ dispute_id: disputeId }),
  });
  if (!res.ok) {
    const fallback = await fetch("/disputes/override", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dispute_id: disputeId }),
    });
    if (!fallback.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Manual override failed: ${res.status}`);
    }
    return fallback.json();
  }
  return res.json();
}

export type SimulationScenario =
  | "winnable_clean"
  | "customer_defect_ticket"
  | "transit_weight_loss"
  | "ambiguous_needs_review"
  | "fraud_no_otp"
  | "obd_clean_delivery"
  | "obd_defective_open_box"
  | "rag_prior_complaint";

export async function simulateWebhook(
  scenario: SimulationScenario,
  amount: number = 3499.0,
  reasonCode: string = "product_not_received"
) {
  const res = await fetch(`${API_BASE}/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scenario, amount, reason_code: reasonCode }),
  });
  if (!res.ok) {
    throw new Error(`Simulation failed: ${res.status}`);
  }
  return res.json();
}
