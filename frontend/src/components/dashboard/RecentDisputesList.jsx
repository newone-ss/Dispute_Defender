import React from "react";
import { formatINR, formatTimeAgo } from "../../utils/formatters";
import { Badge } from "../ui/Badge";
import { OtpPill, GpsPill, WeightPill, PodPill, ObdPill } from "../disputes/TelemetryPills";
import { ArrowRight, Eye } from "lucide-react";
import { Link } from "react-router-dom";

export function RecentDisputesList({ disputes = [], onSelectDispute }) {
  const recent = disputes.slice(0, 6);

  return (
    <div className="bg-white border border-slate-200/90 rounded-xl overflow-hidden shadow-[0_4px_16px_rgba(15,23,42,0.05)]">
      {/* Card Header */}
      <div className="px-5 py-4 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
        <div>
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Live Dispute Ingestion Feed
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Real-time webhook evaluations with physical courier telemetry validation
          </p>
        </div>
        <Link
          to="/disputes"
          className="text-xs font-medium text-emerald-700 hover:text-emerald-800 flex items-center gap-1 transition-colors"
        >
          <span>View All 50 Disputes</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {/* Disputes List / Table */}
      <div className="divide-y divide-slate-100 overflow-x-auto">
        {recent.map((dispute) => {
          const signals = dispute.evidenceSignals || {};
          return (
            <div
              key={dispute.id}
              className="p-4 flex items-center justify-between gap-4 hover:bg-slate-50/80 transition-colors group cursor-pointer"
              onClick={() => onSelectDispute(dispute.id)}
            >
              {/* Left Info: ID & Customer */}
              <div className="min-w-[140px]">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold text-[#172033] group-hover:text-emerald-700 transition-colors">
                    {dispute.id}
                  </span>
                  <ObdPill hasObd={dispute.hasObd} />
                </div>
                <div className="text-[11px] text-slate-500 truncate max-w-[150px]">
                  {dispute.customerName}
                </div>
              </div>

              {/* Amount */}
              <div className="text-right min-w-[90px]">
                <div className="font-mono text-xs font-bold text-[#172033]">
                  {formatINR(dispute.amount)}
                </div>
                <div className="text-[10px] text-slate-400 font-mono">
                  {dispute.reasonDescription || "Chargeback"}
                </div>
              </div>

              {/* Risk Score */}
              <div className="min-w-[80px]">
                <div className="flex items-center gap-1.5">
                  <span className="font-mono text-xs font-bold text-[#172033]">
                    {dispute.riskScore}
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">/100</span>
                </div>
                <div className="w-16 h-1 bg-slate-100 rounded-full overflow-hidden mt-1 border border-slate-200/50">
                  <div
                    className={`h-full rounded-full ${
                      dispute.riskScore >= 80
                        ? "bg-emerald-500"
                        : dispute.riskScore >= 40
                        ? "bg-amber-500"
                        : "bg-rose-500"
                    }`}
                    style={{ width: `${dispute.riskScore}%` }}
                  />
                </div>
              </div>

              {/* Decision Status Badge */}
              <div className="min-w-[130px]">
                <Badge status={dispute.status} size="sm" />
              </div>

              {/* Telemetry Quick Badges */}
              <div className="hidden md:flex items-center gap-1.5 min-w-[200px]">
                <OtpPill verified={signals.doorstepOtp?.verified} />
                <GpsPill distanceMeters={signals.gpsGeofence?.distanceMeters} />
                <WeightPill 
                  deltaPct={signals.weightDelta?.deltaPct} 
                  originGrams={signals.weightDelta?.originGrams}
                  doorstepGrams={signals.weightDelta?.doorstepGrams}
                />
                <PodPill verified={signals.proofOfDelivery?.verified} />
              </div>

              {/* Time Ago */}
              <div className="text-[11px] text-slate-400 min-w-[70px] text-right font-mono hidden sm:block">
                {formatTimeAgo(dispute.timestamp)}
              </div>

              {/* Deep Audit Button */}
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onSelectDispute(dispute.id);
                }}
                className="px-2.5 py-1 text-xs font-medium text-slate-700 hover:text-emerald-700 bg-white hover:bg-slate-50 rounded-lg border border-slate-200 shadow-xs flex items-center gap-1.5 transition-all shrink-0"
              >
                <Eye className="w-3.5 h-3.5" />
                <span>Audit</span>
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
