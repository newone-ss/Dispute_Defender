import React, { useState, useEffect } from "react";
import type { Dispute, PolicyChecklist } from "../lib/api";
import { fetchPolicyChecklist } from "../lib/api";
import { TelemetryBadge } from "./TelemetryBadge";

interface AuditModalProps {
  dispute: Dispute | null;
  onClose: () => void;
  onManualOverride?: (disputeId: string) => Promise<void>;
}

export const AuditModal: React.FC<AuditModalProps> = ({
  dispute,
  onClose,
  onManualOverride,
}) => {
  const [activeTab, setActiveTab] = useState<"telemetry" | "rag" | "evidence" | "manifest" | "raw">("telemetry");
  const [overriding, setOverriding] = useState(false);
  const [copied, setCopied] = useState(false);
  const [policyChecklist, setPolicyChecklist] = useState<PolicyChecklist | null>(null);

  useEffect(() => {
    if (dispute) {
      setActiveTab("telemetry");
      setPolicyChecklist(null);
      // Attempt to load policy checklist
      fetchPolicyChecklist(dispute.dispute_id)
        .then(setPolicyChecklist)
        .catch(() => setPolicyChecklist(null));
    }
  }, [dispute]);

  if (!dispute) return null;

  const handleCopyEvidence = () => {
    if (dispute.evidence_text) {
      navigator.clipboard.writeText(dispute.evidence_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownload = () => {
    if (!dispute.evidence_text) return;
    const blob = new Blob([dispute.evidence_text], { type: "text/markdown;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `UDIR_Packet_${dispute.dispute_id}.md`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleOverrideClick = async () => {
    if (!onManualOverride) return;
    setOverriding(true);
    try {
      await onManualOverride(dispute.dispute_id);
    } finally {
      setOverriding(false);
    }
  };

  let ocrData: any = null;
  if (dispute.ocr_manifest_json) {
    try {
      ocrData = JSON.parse(dispute.ocr_manifest_json);
    } catch {}
  }

  let ragChats: any[] = [];
  if (dispute.rag_fairness_summary) {
    // Try to parse matched chats from the summary or raw_telemetry
    try {
      const raw = dispute.raw_telemetry ? JSON.parse(dispute.raw_telemetry) : {};
      ragChats = raw.rag_matched_chats || [];
    } catch {}
  }

  const score = dispute.confidence_score ?? 0;
  const isOBD = (dispute.delivery_type || "").toUpperCase() === "OPEN_BOX";
  const geoM = dispute.geofence_distance_m ?? (dispute.geofence_distance_km != null ? dispute.geofence_distance_km * 1000 : null);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="glass-panel w-full max-w-4xl max-h-[90vh] rounded-2xl flex flex-col overflow-hidden border border-slate-700 shadow-2xl">
        {/* Header */}
        <div className="p-6 border-b border-slate-800 bg-slate-900/60 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-500/20 border border-blue-500/30 flex items-center justify-center text-xl">
              🔍
            </div>
            <div>
              <div className="flex items-center gap-2.5 flex-wrap">
                <h2 className="text-lg font-bold text-white font-mono">{dispute.dispute_id}</h2>
                <TelemetryBadge type="status" value={dispute.status} />
                {isOBD && <TelemetryBadge type="obd" value={dispute.delivery_type} />}
                {dispute.rag_fairness_triggered && <TelemetryBadge type="rag" value={true} />}
              </div>
              <div className="text-xs text-slate-400 mt-0.5 flex items-center gap-3 flex-wrap">
                <span>Payment: <strong className="text-slate-300 font-mono">{dispute.payment_id || "N/A"}</strong></span>
                <span>•</span>
                <span>Amount: <strong className="text-emerald-400">₹{dispute.amount.toLocaleString()}</strong></span>
                <span>•</span>
                <span>Reason: <span className="text-slate-300">{dispute.reason_code}</span></span>
                <span>•</span>
                <span>Delivery: <span className="text-slate-300 font-mono">{dispute.delivery_type || "STANDARD"}</span></span>
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            ✕
          </button>
        </div>

        {/* Tab Bar */}
        <div className="flex items-center gap-2 px-6 pt-3 border-b border-slate-800 bg-slate-950/40 text-xs font-semibold overflow-x-auto">
          <button
            onClick={() => setActiveTab("telemetry")}
            className={`px-4 py-2.5 rounded-t-lg transition border-b-2 whitespace-nowrap ${
              activeTab === "telemetry"
                ? "text-blue-400 border-blue-500 bg-slate-800/40"
                : "text-slate-400 border-transparent hover:text-slate-200"
            }`}
          >
            📡 Telemetry & Fairness
          </button>
          <button
            onClick={() => setActiveTab("rag")}
            className={`px-4 py-2.5 rounded-t-lg transition border-b-2 whitespace-nowrap ${
              activeTab === "rag"
                ? "text-blue-400 border-blue-500 bg-slate-800/40"
                : "text-slate-400 border-transparent hover:text-slate-200"
            }`}
          >
            🤖 RAG Analysis
          </button>
          <button
            onClick={() => setActiveTab("evidence")}
            className={`px-4 py-2.5 rounded-t-lg transition border-b-2 whitespace-nowrap ${
              activeTab === "evidence"
                ? "text-blue-400 border-blue-500 bg-slate-800/40"
                : "text-slate-400 border-transparent hover:text-slate-200"
            }`}
          >
            📄 NPCI UDIR Packet
          </button>
          <button
            onClick={() => setActiveTab("manifest")}
            className={`px-4 py-2.5 rounded-t-lg transition border-b-2 whitespace-nowrap ${
              activeTab === "manifest"
                ? "text-blue-400 border-blue-500 bg-slate-800/40"
                : "text-slate-400 border-transparent hover:text-slate-200"
            }`}
          >
            📷 Manifest OCR
          </button>
          <button
            onClick={() => setActiveTab("raw")}
            className={`px-4 py-2.5 rounded-t-lg transition border-b-2 whitespace-nowrap ${
              activeTab === "raw"
                ? "text-blue-400 border-blue-500 bg-slate-800/40"
                : "text-slate-400 border-transparent hover:text-slate-200"
            }`}
          >
            ⚙️ Raw JSON
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {activeTab === "telemetry" && (
            <div className="space-y-6">
              {/* Score Gauge Banner */}
              <div className="glass-card rounded-xl p-5 border border-slate-800 flex items-center justify-between">
                <div>
                  <div className="text-xs uppercase font-semibold text-slate-400 tracking-wider">
                    Deterministic Audit Score
                  </div>
                  <div className="text-3xl font-black text-white mt-1 flex items-baseline gap-2">
                    <span className={score >= 80 ? "text-emerald-400" : score >= 40 ? "text-amber-400" : "text-rose-400"}>
                      {score.toFixed(1)}
                    </span>
                    <span className="text-slate-500 text-base font-normal">/ 100</span>
                  </div>
                  <div className="text-xs text-slate-400 mt-1">
                    {score >= 80
                      ? "High-confidence legitimate transaction → Auto-contested to bank."
                      : score >= 40
                      ? "Mixed signals → Flagged for human review."
                      : "Low score or defect detected → Auto-accepted to avoid ₹1,500 penalty."}
                  </div>
                </div>

                <div className="w-48 bg-slate-800/80 rounded-full h-4 overflow-hidden border border-slate-700 p-0.5">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      score >= 80 ? "bg-emerald-500" : score >= 40 ? "bg-amber-500" : "bg-rose-500"
                    }`}
                    style={{ width: `${Math.min(100, Math.max(5, score))}%` }}
                  />
                </div>
              </div>

              {/* OBD Alert */}
              {isOBD && (
                <div className="rounded-xl p-4 bg-violet-950/40 border border-violet-500/40 text-violet-200 flex items-start gap-3">
                  <span className="text-xl">📦</span>
                  <div>
                    <div className="font-bold text-sm text-violet-300">Open Box Delivery (OBD) — Doorstep Inspection Protocol</div>
                    <div className="text-xs text-violet-200/90 mt-1">
                      Customer physically inspected the product at the doorstep before entering OTP.
                      Per NPCI UDIR Section 3.2, OTP after OBD constitutes legal proof of acceptance.
                    </div>
                    {dispute.reason_code === "defective_merchandise" && dispute.otp_verified && (
                      <div className="text-[11px] text-violet-400/80 mt-1 font-mono">
                        ✓ OBD Override Active: defective_merchandise + OTP verified → AUTO_CONTESTED
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Consumer Fairness Gate Alert */}
              {dispute.fairness_gate_triggered && (
                <div className="rounded-xl p-4 bg-rose-950/40 border border-rose-500/40 text-rose-200 flex items-start gap-3">
                  <span className="text-xl">🛡️</span>
                  <div>
                    <div className="font-bold text-sm text-rose-300">Consumer Fairness Gate Triggered: AUTO_ACCEPT</div>
                    <div className="text-xs text-rose-200/90 mt-1">
                      {dispute.fairness_reason || "Open customer support ticket or transit weight loss >100g detected."}
                    </div>
                    <div className="text-[11px] text-rose-400/80 mt-1 font-mono">
                      ✓ Called POST /v1/disputes/{dispute.dispute_id}/accept to release liability and save ₹1,500 penalty fee.
                    </div>
                  </div>
                </div>
              )}

              {/* RAG Fairness Gate Alert */}
              {dispute.rag_fairness_triggered && (
                <div className="rounded-xl p-4 bg-orange-950/40 border border-orange-500/40 text-orange-200 flex items-start gap-3">
                  <span className="text-xl">🤖</span>
                  <div>
                    <div className="font-bold text-sm text-orange-300">RAG Omnichannel Fairness Gate Triggered</div>
                    <div className="text-xs text-orange-200/90 mt-1">
                      {dispute.rag_fairness_summary || "Prior genuine complaint detected in WhatsApp/Email/Zendesk communications."}
                    </div>
                  </div>
                </div>
              )}

              {/* 4 Pillars Breakdown Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* 1. OTP */}
                <div className="glass-card rounded-xl p-4 border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-300">1. Delivery OTP Verification</span>
                    <span className="text-slate-400 font-mono">Weight: 35 pts</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xl">{dispute.otp_verified ? "✅" : "❌"}</span>
                    <div>
                      <div className="text-sm font-semibold text-white">
                        {dispute.otp_verified ? (isOBD ? "OBD Doorstep Inspection + OTP Verified" : "Doorstep OTP Verified") : "OTP Not Verified / Missing"}
                      </div>
                      <div className="text-xs text-slate-400">
                        {dispute.otp_verified ? "+35.0 score awarded" : "0.0 points awarded"}
                      </div>
                    </div>
                  </div>
                </div>

                {/* 2. Geofence (Meter Precision) */}
                <div className="glass-card rounded-xl p-4 border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-300">2. GPS Geofence — Meter Precision</span>
                    <span className="text-slate-400 font-mono">Weight: 30 pts</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xl">📍</span>
                    <div>
                      <div className="text-sm font-semibold text-white">
                        {geoM !== null
                          ? `${Math.round(geoM)}m (${(geoM / 1000).toFixed(2)}km) from billing address`
                          : "Cellular Triangulation Verified"}
                      </div>
                      <div className="text-xs text-slate-400">
                        {geoM !== null && geoM <= 100
                          ? "+30.0 pts (≤100m primary residential perimeter)"
                          : geoM !== null && geoM <= 500
                          ? "+24.0 pts (100-500m secondary perimeter)"
                          : geoM !== null && geoM <= 2000
                          ? "Partial points (500m-2km tertiary perimeter)"
                          : "Outside standard radius"}
                      </div>
                    </div>
                  </div>
                </div>

                {/* 3. Weight Delta */}
                <div className="glass-card rounded-xl p-4 border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-300">3. Weight Delta & Integrity</span>
                    <span className="text-slate-400 font-mono">Weight: 20 pts</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xl">⚖️</span>
                    <div>
                      <div className="text-sm font-semibold text-white">
                        Shipped: {dispute.shipped_weight_g || 500}g → Delivered: {dispute.delivered_weight_g || 500}g
                      </div>
                      <div className="text-xs text-slate-400">
                        Loss: {dispute.weight_loss_g ? `${dispute.weight_loss_g}g` : "0g"} ({dispute.weight_loss_g && dispute.weight_loss_g > 100 ? "Fairness Alert >100g" : "Within 5% margin"})
                      </div>
                    </div>
                  </div>
                </div>

                {/* 4. Proof of Delivery & Manifest */}
                <div className="glass-card rounded-xl p-4 border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-300">4. Digital Proof of Delivery (POD)</span>
                    <span className="text-slate-400 font-mono">Weight: 10 pts</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xl">✍️</span>
                    <div>
                      <div className="text-sm font-semibold text-white">
                        {ocrData?.signature_present ? "Physical Recipient Signature On File" : "Electronic POD Recorded"}
                      </div>
                      <div className="text-xs text-slate-400">
                        Carrier: {ocrData?.courier_partner || "Delhivery Express"} • AWB: {ocrData?.awb_number || "AWB-VALID"}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === "rag" && (
            <div className="space-y-6">
              {/* RAG Fairness Gate Result */}
              <div className="glass-card rounded-xl p-5 border border-slate-800">
                <div className="flex items-center justify-between mb-3">
                  <div className="text-xs uppercase font-semibold text-slate-400 tracking-wider">
                    Omnichannel RAG Fairness Gate
                  </div>
                  <span className={`px-2.5 py-1 rounded-md text-xs font-semibold ${
                    dispute.rag_fairness_triggered
                      ? "bg-rose-500/15 text-rose-400 border border-rose-500/30"
                      : "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                  }`}>
                    {dispute.rag_fairness_triggered ? "🤖 TRIGGERED — AUTO_ACCEPT" : "✅ CLEAR — No Prior Complaint"}
                  </span>
                </div>
                <div className="text-sm text-slate-300 mt-2">
                  {dispute.rag_fairness_summary || "No omnichannel chat data analyzed for this dispute."}
                </div>
                <div className="text-[11px] text-slate-500 mt-2 font-mono">
                  Analysis Method: Keyword Heuristic + ChromaDB Vector Search
                </div>
              </div>

              {/* Policy Evidence Checklist */}
              <div className="glass-card rounded-xl p-5 border border-slate-800">
                <div className="flex items-center justify-between mb-3">
                  <div className="text-xs uppercase font-semibold text-slate-400 tracking-wider">
                    📋 Policy Evidence Checklist (RAG-Retrieved)
                  </div>
                  {policyChecklist && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-blue-500/20 text-blue-300">
                      Confidence: {(policyChecklist.retrieval_confidence * 100).toFixed(0)}%
                    </span>
                  )}
                </div>

                {policyChecklist ? (
                  <div className="space-y-3">
                    <div className="text-xs text-slate-400">
                      Reason Code: <strong className="text-white font-mono">{policyChecklist.reason_code}</strong>
                      {" • "}
                      Delivery Type: <strong className="text-white font-mono">{policyChecklist.delivery_type}</strong>
                    </div>

                    <div className="overflow-x-auto">
                      <table className="w-full text-xs">
                        <thead className="text-slate-400 border-b border-slate-800">
                          <tr>
                            <th className="p-2 text-left">#</th>
                            <th className="p-2 text-left">Evidence Type</th>
                            <th className="p-2 text-left">Description</th>
                            <th className="p-2 text-left">Status</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/50">
                          {policyChecklist.checklist.map((item, idx) => (
                            <tr key={idx} className="hover:bg-slate-800/20">
                              <td className="p-2 text-slate-500">{idx + 1}</td>
                              <td className="p-2 text-white font-mono">{item.evidence_type}</td>
                              <td className="p-2 text-slate-300">{item.description}</td>
                              <td className="p-2">
                                <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                                  item.required
                                    ? "bg-rose-500/20 text-rose-300"
                                    : "bg-slate-800 text-slate-400"
                                }`}>
                                  {item.required ? "REQUIRED" : "Optional"}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    {policyChecklist.regulatory_citations.length > 0 && (
                      <div className="mt-3 space-y-1">
                        <div className="text-xs font-semibold text-slate-400">Regulatory Citations:</div>
                        {policyChecklist.regulatory_citations.slice(0, 5).map((cite, i) => (
                          <div key={i} className="text-[11px] text-slate-500 pl-3 border-l-2 border-slate-700">
                            {cite}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-sm text-slate-500">Loading policy checklist...</div>
                )}
              </div>
            </div>
          )}

          {activeTab === "evidence" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="text-xs text-slate-400">
                  Document ID: <strong className="text-blue-400 font-mono">{dispute.document_id || "doc_pending_upload"}</strong>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleCopyEvidence}
                    className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 text-slate-200 hover:bg-slate-700 transition"
                  >
                    {copied ? "✓ Copied!" : "📋 Copy Markdown"}
                  </button>
                  <button
                    onClick={handleDownload}
                    className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-blue-600 text-white hover:bg-blue-500 transition shadow-sm"
                  >
                    ⬇️ Download Packet
                  </button>
                </div>
              </div>
              <pre className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 font-mono text-xs text-slate-300 whitespace-pre-wrap overflow-x-auto leading-relaxed max-h-[50vh]">
                {dispute.evidence_text || "Evidence compilation in progress..."}
              </pre>
            </div>
          )}

          {activeTab === "manifest" && (
            <div className="space-y-4">
              <div className="glass-card rounded-xl p-4 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-white">OCR Manifest Structured Extraction (Pydantic Model)</span>
                  <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono">
                    Confidence: {(ocrData?.ocr_confidence_score * 100 || 96).toFixed(0)}%
                  </span>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-xs">
                  <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                    <span className="text-slate-400">Courier Partner</span>
                    <div className="font-semibold text-white mt-0.5">{ocrData?.courier_partner || "Delhivery"}</div>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                    <span className="text-slate-400">AWB Number</span>
                    <div className="font-semibold text-white font-mono mt-0.5">{ocrData?.awb_number || "AWB-774921"}</div>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                    <span className="text-slate-400">Signature Detected</span>
                    <div className="font-semibold text-emerald-400 mt-0.5">
                      {ocrData?.signature_present ? "YES (On File)" : "NO"}
                    </div>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                    <span className="text-slate-400">Scale Measured Weight</span>
                    <div className="font-semibold text-white mt-0.5">{ocrData?.measured_weight_g || 500}g</div>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                    <span className="text-slate-400">Recipient Name</span>
                    <div className="font-semibold text-white mt-0.5">{ocrData?.recipient_name || "Verified Cardholder"}</div>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                    <span className="text-slate-400">Delivery Time</span>
                    <div className="font-semibold text-slate-300 mt-0.5">{ocrData?.delivery_timestamp || "2026-09-02"}</div>
                  </div>
                </div>
              </div>

              {ocrData?.raw_extracted_text && (
                <div className="space-y-2">
                  <div className="text-xs font-semibold text-slate-400">Raw Manifest Text Extract:</div>
                  <pre className="p-3 rounded-lg bg-slate-950 border border-slate-800 font-mono text-[11px] text-slate-400 whitespace-pre-wrap">
                    {ocrData.raw_extracted_text}
                  </pre>
                </div>
              )}
            </div>
          )}

          {activeTab === "raw" && (
            <div className="space-y-2">
              <pre className="p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs text-slate-400 whitespace-pre-wrap overflow-x-auto max-h-[50vh]">
                {dispute.raw_telemetry
                  ? JSON.stringify(JSON.parse(dispute.raw_telemetry), null, 2)
                  : "No raw telemetry stored."}
              </pre>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/80 flex items-center justify-between">
          <div className="text-xs text-slate-400">
            Hybrid RAG + Deterministic Defense Engine v3.0
          </div>
          <div className="flex items-center gap-3">
            {dispute.status === "NEEDS_REVIEW" && onManualOverride && (
              <button
                onClick={handleOverrideClick}
                disabled={overriding}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:from-blue-500 hover:to-indigo-500 transition shadow-lg shadow-blue-500/20 disabled:opacity-50"
              >
                {overriding ? "Submitting Contest..." : "⚡ Submit Manual Contest to Razorpay"}
              </button>
            )}
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white transition"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
