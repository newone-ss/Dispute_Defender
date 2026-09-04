import React, { useState } from "react";
import { useDashboard } from "../hooks/useDashboard";
import { useDisputes } from "../hooks/useDisputes";
import { KpiGrid } from "../components/dashboard/KpiGrid";
import { DecisionDistributionChart } from "../components/dashboard/DecisionDistributionChart";
import { TelemetryHealthStats } from "../components/dashboard/TelemetryHealthStats";
import { RecentDisputesList } from "../components/dashboard/RecentDisputesList";
import { DeepAuditModal } from "../components/audit/DeepAuditModal";
import { Loader2, RefreshCw } from "lucide-react";

export function Dashboard() {
  const { data: metrics, isLoading: loadingMetrics, refetch: refetchMetrics } = useDashboard();
  const { disputes, isLoading: loadingDisputes, refetch: refetchDisputes } = useDisputes();
  const [selectedDisputeId, setSelectedDisputeId] = useState(null);

  const handleRefresh = () => {
    refetchMetrics();
    refetchDisputes();
  };

  if (loadingMetrics && !metrics) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-slate-500 gap-3 text-xs font-mono">
        <Loader2 className="w-6 h-6 animate-spin text-emerald-600" />
        <span>Loading operational telemetry and financial impact benchmarks...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Controls Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-slate-200/80">
        <div>
          <h2 className="text-base font-bold text-[#172033]">
            Financial ROI & Telemetry Overview
          </h2>
          <p className="text-xs text-slate-500">
            Automated dispute defense pipeline safeguarding merchant liability
          </p>
        </div>

        <button
          type="button"
          onClick={handleRefresh}
          className="self-start sm:self-auto px-3 py-1.5 rounded-lg bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 text-xs font-medium flex items-center gap-1.5 transition-colors shadow-xs"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Feed</span>
        </button>
      </div>

      {/* 1. Top KPI Grid */}
      <KpiGrid metrics={metrics} />

      {/* 2. Decision Distribution & Timeline */}
      <DecisionDistributionChart metrics={metrics} />

      {/* 3. Physical Courier Telemetry Compliance */}
      <TelemetryHealthStats compliance={metrics?.telemetryCompliance} />

      {/* 4. Live Recent Disputes Feed */}
      <RecentDisputesList
        disputes={disputes}
        onSelectDispute={(id) => setSelectedDisputeId(id)}
      />

      {/* Deep Audit Modal */}
      <DeepAuditModal
        disputeId={selectedDisputeId}
        isOpen={Boolean(selectedDisputeId)}
        onClose={() => setSelectedDisputeId(null)}
      />
    </div>
  );
}
