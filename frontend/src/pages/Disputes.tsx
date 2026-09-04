import React, { useEffect, useState } from "react";
import { fetchDisputes, manualOverride } from "../lib/api";
import type { Dispute } from "../lib/api";
import { TelemetryBadge } from "../components/TelemetryBadge";
import { AuditModal } from "../components/AuditModal";

export const Disputes: React.FC = () => {
  const [disputes, setDisputes] = useState<Dispute[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedDispute, setSelectedDispute] = useState<Dispute | null>(null);
  const [overridingId, setOverridingId] = useState<string | null>(null);

  const loadDisputes = async () => {
    try {
      setLoading(true);
      const res = await fetchDisputes(
        statusFilter === "ALL" ? undefined : statusFilter,
        searchTerm,
        0,
        100
      );
      setDisputes(res.disputes);
      setTotal(res.total);
    } catch (err) {
      console.error("Failed to load disputes:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDisputes();
  }, [statusFilter, searchTerm]);

  const handleManualOverride = async (disputeId: string, operatorNote?: string) => {
    setOverridingId(disputeId);
    try {
      await manualOverride(disputeId, "contest", operatorNote || "Verified physical courier telemetry & signed manifest");
      await loadDisputes();
      if (selectedDispute && (selectedDispute.dispute_id === disputeId || selectedDispute.razorpay_dispute_id === disputeId)) {
        setSelectedDispute((prev) => (prev ? { ...prev, status: "MANUALLY_CONTESTED" } : null));
      }
    } catch (err: any) {
      alert(`Manual contest failed: ${err.message}`);
    } finally {
      setOverridingId(null);
    }
  };

  const statuses = [
    { id: "ALL", label: "All Disputes" },
    { id: "AUTO_CONTESTED", label: "Auto Contested" },
    { id: "NEEDS_REVIEW", label: "Needs Review" },
    { id: "AUTO_ACCEPTED", label: "Auto Accepted" },
    { id: "MANUALLY_CONTESTED", label: "Manually Contested" },
  ];

  return (
    <div className="space-y-6 animate-fade-in max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-black text-white tracking-tight flex items-center gap-3">
            <span>⚔️</span> Disputes & Telemetry Queue
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time audit of intercepted chargebacks with OBD routing, RAG fairness gate, and physical delivery proofs.
          </p>
        </div>

        <div className="text-xs font-mono text-slate-400 bg-slate-900 px-3 py-2 rounded-xl border border-slate-800">
          Total Filtered: <strong className="text-white">{total}</strong>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="glass-card rounded-xl p-4 border border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Status Filter Tabs */}
        <div className="flex flex-wrap items-center gap-1.5 w-full md:w-auto">
          {statuses.map((st) => (
            <button
              key={st.id}
              onClick={() => setStatusFilter(st.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                statusFilter === st.id
                  ? "bg-blue-600 text-white shadow-sm"
                  : "bg-slate-800/60 text-slate-400 hover:text-slate-200 hover:bg-slate-800"
              }`}
            >
              {st.label}
            </button>
          ))}
        </div>

        {/* Search Input */}
        <div className="w-full md:w-72">
          <input
            type="text"
            placeholder="Search dispute, payment, or order ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-700 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </div>
      </div>

      {/* Table */}
      <div className="glass-card rounded-2xl border border-slate-800 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/90 text-slate-400 uppercase tracking-wider text-[11px] border-b border-slate-800">
              <tr>
                <th className="p-4">Dispute & Order Details</th>
                <th className="p-4">Disputed Amount</th>
                <th className="p-4">Audit Score</th>
                <th className="p-4">Physical Telemetry Checklist</th>
                <th className="p-4">Pipeline Decision</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
              {loading ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-slate-500 font-sans">
                    Loading dispute telemetry records...
                  </td>
                </tr>
              ) : disputes.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-slate-500 font-sans">
                    No disputes match the selected filters.
                  </td>
                </tr>
              ) : (
                disputes.map((d) => (
                  <tr key={d.id} className="hover:bg-slate-800/30 transition">
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-white">{d.dispute_id}</span>
                        {d.delivery_type === "OPEN_BOX" && (
                          <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-violet-500/20 text-violet-300 border border-violet-600/30">OBD</span>
                        )}
                      </div>
                      <div className="text-[10px] text-slate-400 font-normal mt-0.5">
                        Order: <span className="text-slate-300">{d.order_id || "N/A"}</span> • {d.reason_code}
                      </div>
                    </td>

                    <td className="p-4 font-bold text-slate-100">
                      ₹{d.amount.toLocaleString()}
                    </td>

                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <span
                          className={`font-bold ${
                            (d.confidence_score || 0) >= 80
                              ? "text-emerald-400"
                              : (d.confidence_score || 0) >= 40
                              ? "text-amber-400"
                              : "text-rose-400"
                          }`}
                        >
                          {(d.confidence_score || 0).toFixed(1)}/100
                        </span>
                      </div>
                    </td>

                    <td className="p-4 font-sans">
                      <div className="flex flex-wrap gap-1.5 items-center">
                        <TelemetryBadge type="otp" value={d.otp_verified} />
                        <TelemetryBadge type="geofence" value={d.geofence_distance_km} />
                        <TelemetryBadge type="weight" value={d.weight_loss_g} />
                        <TelemetryBadge type="defect" value={d.defect_ticket_open} />
                        <TelemetryBadge type="obd" value={d.delivery_type} />
                        <TelemetryBadge type="rag" value={d.rag_fairness_triggered} />
                      </div>
                    </td>

                    <td className="p-4 font-sans">
                      <div className="flex flex-col gap-1 items-start">
                        <TelemetryBadge type="status" value={d.status} />
                        {d.fairness_gate_triggered && (
                          <span className="text-[10px] text-rose-400 font-medium">
                            Fairness Gate: Zero Liability
                          </span>
                        )}
                        {d.rag_fairness_triggered && !d.fairness_gate_triggered && (
                          <span className="text-[10px] text-orange-400 font-medium">
                            RAG: Prior Complaint
                          </span>
                        )}
                      </div>
                    </td>

                    <td className="p-4 text-right font-sans">
                      <div className="flex items-center justify-end gap-2">
                        {d.status === "NEEDS_REVIEW" && (
                          <button
                            onClick={() => handleManualOverride(d.dispute_id)}
                            disabled={overridingId === d.dispute_id}
                            className="px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30 hover:bg-amber-500/30 transition disabled:opacity-50"
                            title="Submit manual representment to Razorpay"
                          >
                            {overridingId === d.dispute_id ? "Contesting..." : "⚡ Override"}
                          </button>
                        )}
                        <button
                          onClick={() => setSelectedDispute(d)}
                          className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 text-blue-400 hover:bg-blue-600 hover:text-white transition"
                        >
                          Inspect 🔍
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal Inspector */}
      <AuditModal
        dispute={selectedDispute}
        onClose={() => setSelectedDispute(null)}
        onManualOverride={handleManualOverride}
      />
    </div>
  );
};

export default Disputes;
