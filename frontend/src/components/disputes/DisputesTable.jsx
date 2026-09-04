import React from "react";
import { formatINR, formatTimeAgo } from "../../utils/formatters";
import { Badge } from "../ui/Badge";
import { OtpPill, GpsPill, WeightPill, PodPill, ObdPill } from "./TelemetryPills";
import { Eye, Smartphone, AlertCircle } from "lucide-react";

export function DisputesTable({ disputes = [], onSelectDispute, loading = false }) {
  if (loading) {
    return (
      <div className="bg-white border border-slate-200/90 rounded-xl p-12 text-center text-slate-400 text-xs font-mono animate-pulse shadow-[0_4px_16px_rgba(15,23,42,0.05)]">
        Loading dispute telemetry records...
      </div>
    );
  }

  if (disputes.length === 0) {
    return (
      <div className="bg-white border border-slate-200/90 rounded-xl p-12 text-center space-y-2 shadow-[0_4px_16px_rgba(15,23,42,0.05)]">
        <AlertCircle className="w-8 h-8 text-slate-400 mx-auto" />
        <h4 className="text-sm font-semibold text-[#172033]">No disputes found</h4>
        <p className="text-xs text-slate-500">
          Try clearing your filters or search keywords to view other records.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white border border-slate-200/90 rounded-xl overflow-hidden shadow-[0_4px_16px_rgba(15,23,42,0.05)]">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-slate-700">
          <thead className="bg-slate-50 text-[11px] font-semibold text-slate-500 uppercase tracking-wider border-b border-slate-200">
            <tr>
              <th className="py-3 px-4">Dispute</th>
              <th className="py-3 px-4">Amount</th>
              <th className="py-3 px-4">Risk Score</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4">Doorstep OTP</th>
              <th className="py-3 px-4">GPS Offset</th>
              <th className="py-3 px-4">Weight Delta</th>
              <th className="py-3 px-4">POD</th>
              <th className="py-3 px-4">Device</th>
              <th className="py-3 px-4 text-right">Age</th>
              <th className="py-3 px-4 text-center">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 font-sans">
            {disputes.map((dispute) => {
              const signals = dispute.evidenceSignals || {};

              return (
                <tr
                  key={dispute.id}
                  onClick={() => onSelectDispute(dispute.id)}
                  className="hover:bg-slate-50/80 transition-colors cursor-pointer group"
                >
                  {/* Dispute Identifier */}
                  <td className="py-3.5 px-4">
                    <div className="flex items-center gap-1.5">
                      <span className="font-mono font-bold text-[#172033] group-hover:text-emerald-700 transition-colors">
                        {dispute.id}
                      </span>
                      <ObdPill hasObd={dispute.hasObd} />
                    </div>
                    <div className="text-[11px] text-slate-500 truncate max-w-[140px]">
                      {dispute.customerName}
                    </div>
                  </td>

                  {/* Disputed Amount */}
                  <td className="py-3.5 px-4 font-mono font-bold text-[#172033] whitespace-nowrap">
                    {formatINR(dispute.amount)}
                  </td>

                  {/* Risk Score */}
                  <td className="py-3.5 px-4 whitespace-nowrap">
                    <div className="flex items-center gap-1.5">
                      <span className="font-mono font-bold text-[#172033]">
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
                  </td>

                  {/* Status Badge */}
                  <td className="py-3.5 px-4 whitespace-nowrap">
                    <Badge status={dispute.status} size="sm" />
                  </td>

                  {/* Doorstep OTP */}
                  <td className="py-3.5 px-4 whitespace-nowrap">
                    <OtpPill verified={signals.doorstepOtp?.verified} />
                  </td>

                  {/* GPS Offset */}
                  <td className="py-3.5 px-4 whitespace-nowrap">
                    <GpsPill distanceMeters={signals.gpsGeofence?.distanceMeters} />
                  </td>

                  {/* Weight Delta */}
                  <td className="py-3.5 px-4 whitespace-nowrap">
                    <WeightPill
                      deltaPct={signals.weightDelta?.deltaPct}
                      originGrams={signals.weightDelta?.originGrams}
                      doorstepGrams={signals.weightDelta?.doorstepGrams}
                    />
                  </td>

                  {/* POD */}
                  <td className="py-3.5 px-4 whitespace-nowrap">
                    <PodPill verified={signals.proofOfDelivery?.verified} />
                  </td>

                  {/* Device Fingerprint */}
                  <td className="py-3.5 px-4 whitespace-nowrap">
                    {signals.deviceFingerprint?.verified ? (
                      <span className="inline-flex items-center gap-1 text-[11px] font-mono text-emerald-700 font-medium">
                        <Smartphone className="w-3 h-3" /> Match
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[11px] font-mono text-slate-400">
                        <Smartphone className="w-3 h-3" /> New
                      </span>
                    )}
                  </td>

                  {/* Age */}
                  <td className="py-3.5 px-4 text-right font-mono text-[11px] text-slate-400 whitespace-nowrap">
                    {formatTimeAgo(dispute.timestamp)}
                  </td>

                  {/* Action */}
                  <td className="py-3.5 px-4 text-center whitespace-nowrap">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectDispute(dispute.id);
                      }}
                      className="px-2.5 py-1 text-xs font-medium text-slate-700 hover:text-emerald-700 bg-white hover:bg-slate-50 rounded-lg border border-slate-200 shadow-xs inline-flex items-center gap-1.5 transition-all"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>Audit</span>
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
