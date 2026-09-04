import React, { useEffect, useState } from "react";
import { fetchMetrics, fetchDisputes, simulateWebhook, manualOverride } from "../lib/api";
import type { Metrics, Dispute, SimulationScenario } from "../lib/api";
import { MetricCards } from "../components/MetricCards";
import { TelemetryBadge } from "../components/TelemetryBadge";
import { AuditModal } from "../components/AuditModal";

export const Dashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [recentDisputes, setRecentDisputes] = useState<Dispute[]>([]);
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);
  const [selectedDispute, setSelectedDispute] = useState<Dispute | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [m, d] = await Promise.all([fetchMetrics(), fetchDisputes(undefined, undefined, 0, 8)]);
      setMetrics(m);
      setRecentDisputes(d.disputes);
    } catch (err: any) {
      console.error("Failed to load dashboard data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000); // 10s auto-refresh
    return () => clearInterval(interval);
  }, []);

  const handleSimulate = async (scenario: SimulationScenario) => {
    setSimulating(true);
    setStatusMessage(null);
    try {
      await simulateWebhook(scenario);
      setStatusMessage(`✨ Webhook simulated for scenario '${scenario}'. Hybrid RAG + Deterministic pipeline running.`);
      setTimeout(loadData, 1200);
    } catch (err: any) {
      setStatusMessage(`❌ Simulation failed: ${err.message}`);
    } finally {
      setSimulating(false);
    }
  };

  const handleManualOverride = async (disputeId: string) => {
    try {
      await manualOverride(disputeId);
      await loadData();
      if (selectedDispute && selectedDispute.dispute_id === disputeId) {
        setSelectedDispute((prev) => (prev ? { ...prev, status: "MANUALLY_CONTESTED" } : null));
      }
    } catch (err: any) {
      alert(`Manual override failed: ${err.message}`);
    }
  };

  return (
    <div className="space-y-8 animate-fade-in max-w-7xl mx-auto pb-12">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-black text-white tracking-tight flex items-center gap-3">
            <span>🛡️</span> Financial Risk & Chargeback Defense
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Hybrid RAG + Deterministic audit pipeline with OBD routing, omnichannel fairness gating, and NPCI UDIR evidence drafting.
          </p>
        </div>

        <button
          onClick={loadData}
          className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition flex items-center gap-2 self-start md:self-auto border border-slate-700"
        >
          <span>🔄</span> Refresh Telemetry
        </button>
      </div>

      {/* Financial Metric Cards */}
      <MetricCards metrics={metrics} loading={loading} />

      {/* Interactive Scenario Simulation Bar */}
      <div className="glass-card rounded-2xl p-6 border border-slate-800 relative overflow-hidden">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-amber-400 font-bold text-xs uppercase tracking-wider">Interactive Webhook Simulator</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-blue-500/20 text-blue-300">Hybrid RAG + Deterministic</span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Dispatch simulated disputes with OBD routing, RAG fairness gate, and meter-precision GPS telemetry.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => handleSimulate("winnable_clean")}
              disabled={simulating}
              className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-emerald-600/20 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-600/30 transition disabled:opacity-50"
            >
              🚀 Clean Delivery
            </button>
            <button
              onClick={() => handleSimulate("obd_clean_delivery")}
              disabled={simulating}
              className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-violet-600/20 text-violet-300 border border-violet-500/30 hover:bg-violet-600/30 transition disabled:opacity-50"
            >
              📦 OBD Clean
            </button>
            <button
              onClick={() => handleSimulate("obd_defective_open_box")}
              disabled={simulating}
              className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-violet-600/20 text-violet-300 border border-violet-500/30 hover:bg-violet-600/30 transition disabled:opacity-50"
            >
              📦 OBD Defective
            </button>
            <button
              onClick={() => handleSimulate("rag_prior_complaint")}
              disabled={simulating}
              className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-orange-600/20 text-orange-300 border border-orange-500/30 hover:bg-orange-600/30 transition disabled:opacity-50"
            >
              🤖 RAG Complaint
            </button>
            <button
              onClick={() => handleSimulate("customer_defect_ticket")}
              disabled={simulating}
              className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-rose-600/20 text-rose-300 border border-rose-500/30 hover:bg-rose-600/30 transition disabled:opacity-50"
            >
              🎫 Defect Ticket
            </button>
            <button
              onClick={() => handleSimulate("transit_weight_loss")}
              disabled={simulating}
              className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-amber-600/20 text-amber-300 border border-amber-500/30 hover:bg-amber-600/30 transition disabled:opacity-50"
            >
              ⚖️ Weight Loss
            </button>
            <button
              onClick={() => handleSimulate("ambiguous_needs_review")}
              disabled={simulating}
              className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-800 text-slate-300 border border-slate-700 hover:bg-slate-700 transition disabled:opacity-50"
            >
              ⚠️ Ambiguous
            </button>
          </div>
        </div>

        {statusMessage && (
          <div className="mt-3 text-xs font-mono text-emerald-300 bg-emerald-950/40 p-2.5 rounded-lg border border-emerald-800/40">
            {statusMessage}
          </div>
        )}
      </div>

      {/* Decision Distribution Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="glass-card rounded-xl p-5 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-emerald-400">AUTO CONTESTED</span>
            <span className="text-lg font-black text-white">{metrics?.auto_contested_count || 0}</span>
          </div>
          <div className="text-xs text-slate-400">
            Score &gt; 80 or OBD Override. Conclusive telemetry, verified GPS ≤100m, and intact weight. Representment uploaded.
          </div>
          <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
            <div
              className="bg-emerald-500 h-full rounded-full"
              style={{
                width: `${
                  metrics && metrics.total_disputes > 0
                    ? (metrics.auto_contested_count / metrics.total_disputes) * 100
                    : 60
                }%`,
              }}
            />
          </div>
        </div>

        <div className="glass-card rounded-xl p-5 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-amber-400">NEEDS REVIEW</span>
            <span className="text-lg font-black text-white">{metrics?.needs_review_count || 0}</span>
          </div>
          <div className="text-xs text-slate-400">
            Score 40–80 or standard defective merchandise. Requires merchant risk officer manual verification.
          </div>
          <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
            <div
              className="bg-amber-500 h-full rounded-full"
              style={{
                width: `${
                  metrics && metrics.total_disputes > 0
                    ? (metrics.needs_review_count / metrics.total_disputes) * 100
                    : 15
                }%`,
              }}
            />
          </div>
        </div>

        <div className="glass-card rounded-xl p-5 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-rose-400">AUTO ACCEPTED</span>
            <span className="text-lg font-black text-white">{metrics?.auto_accepted_count || 0}</span>
          </div>
          <div className="text-xs text-slate-400">
            Fairness Gate (defect/loss/RAG complaint) or Score &lt; 40. Released liability, saving ₹1,500 bank penalty per dispute.
          </div>
          <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
            <div
              className="bg-rose-500 h-full rounded-full"
              style={{
                width: `${
                  metrics && metrics.total_disputes > 0
                    ? (metrics.auto_accepted_count / metrics.total_disputes) * 100
                    : 25
                }%`,
              }}
            />
          </div>
        </div>
      </div>

      {/* Recent Telemetry Stream */}
      <div className="glass-card rounded-2xl border border-slate-800 overflow-hidden">
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-white tracking-tight">Recent Dispute Interceptions</h2>
            <p className="text-xs text-slate-400 mt-0.5">Live chargebacks audited with hybrid RAG + physical courier telemetry</p>
          </div>
          <a
            href="/disputes"
            className="text-xs font-semibold text-blue-400 hover:text-blue-300 transition flex items-center gap-1"
          >
            View All ({metrics?.total_disputes || 0}) →
          </a>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 text-slate-400 uppercase tracking-wider text-[11px] border-b border-slate-800">
              <tr>
                <th className="p-4">Dispute ID</th>
                <th className="p-4">Amount</th>
                <th className="p-4">Audit Score</th>
                <th className="p-4">Courier Telemetry</th>
                <th className="p-4">Decision</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
              {recentDisputes.map((d) => (
                <tr key={d.id} className="hover:bg-slate-800/30 transition">
                  <td className="p-4 font-bold text-white">
                    <div className="flex items-center gap-2">
                      {d.dispute_id}
                      {d.delivery_type === "OPEN_BOX" && (
                        <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-violet-500/20 text-violet-300 border border-violet-600/30">OBD</span>
                      )}
                    </div>
                    <div className="text-[10px] text-slate-500 font-normal">{d.reason_code}</div>
                  </td>
                  <td className="p-4 font-bold text-slate-100">
                    ₹{d.amount.toLocaleString()}
                  </td>
                  <td className="p-4">
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
                    <TelemetryBadge type="status" value={d.status} />
                  </td>
                  <td className="p-4 text-right font-sans">
                    <button
                      onClick={() => setSelectedDispute(d)}
                      className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 text-blue-400 hover:bg-blue-600 hover:text-white transition"
                    >
                      Inspect Audit 🔍
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Deep Audit Modal */}
      <AuditModal
        dispute={selectedDispute}
        onClose={() => setSelectedDispute(null)}
        onManualOverride={handleManualOverride}
      />
    </div>
  );
};

export default Dashboard;
