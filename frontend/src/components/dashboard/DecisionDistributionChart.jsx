import React, { useState } from "react";
import { formatINR } from "../../utils/formatters";

export function DecisionDistributionChart({ metrics }) {
  if (!metrics) return null;

  const distribution = metrics.decisionDistribution || [];
  const timelineData = metrics.activityTimeline || [
    { hour: "08:00", contested: 2, accepted: 1, reviewed: 0 },
    { hour: "10:00", contested: 4, accepted: 2, reviewed: 1 },
    { hour: "12:00", contested: 6, accepted: 1, reviewed: 2 },
    { hour: "14:00", contested: 5, accepted: 3, reviewed: 1 },
    { hour: "16:00", contested: 7, accepted: 2, reviewed: 2 },
    { hour: "18:00", contested: 3, accepted: 1, reviewed: 0 },
  ];

  const [hoveredIdx, setHoveredIdx] = useState(null);

  // Maximum value for dynamic scaling
  const maxVal = Math.max(
    ...timelineData.map((d) => Math.max(d.contested || 0, d.accepted || 0)),
    6
  );

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      {/* 1. Decision Breakdown & Progress Bars */}
      <div className="lg:col-span-1 bg-white border border-slate-200/90 rounded-xl p-5 shadow-[0_2px_8px_rgba(15,23,42,0.04)] flex flex-col justify-between">
        <div>
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
            Decision Distribution
          </h3>
          <p className="text-xs text-slate-500 mb-4">
            Deterministic routing by scoring policy & fairness gate
          </p>

          {/* Segmented Visual Bar */}
          <div className="h-3.5 w-full bg-slate-100 rounded-full overflow-hidden flex gap-0.5 p-0.5 border border-slate-200">
            <div 
              style={{ width: "64%" }} 
              className="h-full bg-emerald-500 rounded-l-full transition-all duration-500" 
              title="AUTO_CONTESTED: 64%"
            />
            <div 
              style={{ width: "12%" }} 
              className="h-full bg-amber-500 transition-all duration-500" 
              title="NEEDS_REVIEW: 12%"
            />
            <div 
              style={{ width: "24%" }} 
              className="h-full bg-rose-500 rounded-r-full transition-all duration-500" 
              title="AUTO_ACCEPTED: 24%"
            />
          </div>

          {/* Detailed Metric Rows */}
          <div className="mt-5 space-y-2.5">
            {distribution.map((item) => (
              <div 
                key={item.status} 
                className="p-3 rounded-lg bg-slate-50/80 border border-slate-200/80 flex items-center justify-between"
              >
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span 
                      className="w-2 h-2 rounded-full" 
                      style={{ backgroundColor: item.color }} 
                    />
                    <span className="text-xs font-semibold text-[#172033]">{item.label}</span>
                    <span className="text-[10px] font-mono text-slate-500">
                      ({item.percentage}%)
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-500">
                    {item.count} cases
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-xs font-bold font-mono text-[#172033]">
                    {formatINR(item.amountINR)}
                  </div>
                  <div className="text-[10px] text-slate-500">
                    {item.status === "AUTO_CONTESTED" ? "Contested" : item.status === "AUTO_ACCEPTED" ? "Liability Released" : "In Review Queue"}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Total Exposure Footer */}
        <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
          <span className="text-slate-500">Total Dispute Exposure</span>
          <span className="font-mono font-bold text-[#172033]">
            {formatINR(metrics.totalExposureINR)}
          </span>
        </div>
      </div>

      {/* 2. Real-Time Telemetry Resolution Activity Chart */}
      <div className="lg:col-span-2 bg-white border border-slate-200/90 rounded-xl p-5 shadow-[0_2px_8px_rgba(15,23,42,0.04)] flex flex-col justify-between">
        <div className="flex items-center justify-between mb-2">
          <div>
            <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Dispute Processing Timeline
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Hourly resolution volume across the active working shift
            </p>
          </div>
          <div className="flex items-center gap-3 text-xs">
            <span className="flex items-center gap-1.5 text-emerald-700 text-[11px] font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-600" /> Contested
            </span>
            <span className="flex items-center gap-1.5 text-rose-700 text-[11px] font-medium">
              <span className="w-2 h-2 rounded-full bg-rose-600" /> Liability Released
            </span>
          </div>
        </div>

        {/* Clean, Modern Dual Bar Timeline Chart */}
        <div className="relative h-56 w-full pt-4 flex flex-col justify-end">
          {/* Subtle horizontal grid lines */}
          <div className="absolute inset-0 flex flex-col justify-between pointer-events-none pb-7 pt-2 pr-2">
            <div className="border-b border-dashed border-slate-200/80 w-full flex justify-between text-[10px] text-slate-400 font-mono">
              <span>{maxVal}</span>
            </div>
            <div className="border-b border-dashed border-slate-200/80 w-full flex justify-between text-[10px] text-slate-400 font-mono">
              <span>{Math.round(maxVal / 2)}</span>
            </div>
            <div className="border-b border-slate-200 w-full flex justify-between text-[10px] text-slate-400 font-mono">
              <span>0</span>
            </div>
          </div>

          {/* Vertical Columns */}
          <div className="relative z-10 grid grid-cols-6 gap-2 sm:gap-6 h-40 items-end px-3 sm:px-6">
            {timelineData.map((item, idx) => {
              const contested = item.contested || 0;
              const accepted = item.accepted || 0;
              const contestedHeightPct = Math.min(100, (contested / maxVal) * 100);
              const acceptedHeightPct = Math.min(100, (accepted / maxVal) * 100);
              const isHovered = hoveredIdx === idx;

              return (
                <div
                  key={item.hour || idx}
                  className="relative flex flex-col items-center h-full justify-end group cursor-pointer"
                  onMouseEnter={() => setHoveredIdx(idx)}
                  onMouseLeave={() => setHoveredIdx(null)}
                >
                  {/* Floating Tooltip */}
                  {isHovered && (
                    <div className="absolute -top-12 z-30 px-3 py-1.5 rounded-lg bg-slate-900 text-white text-[11px] font-mono whitespace-nowrap shadow-xl border border-slate-700 animate-in fade-in duration-100">
                      <div className="font-semibold text-slate-200 text-center">{item.hour} Shift</div>
                      <div className="flex items-center gap-2 text-[10px] mt-0.5">
                        <span className="text-emerald-400 font-bold">{contested} Contested</span>
                        <span className="text-slate-500">|</span>
                        <span className="text-rose-400 font-bold">{accepted} Released</span>
                      </div>
                    </div>
                  )}

                  {/* Dual Bar Column */}
                  <div className="flex items-end gap-1 sm:gap-1.5 h-full w-full max-w-[40px] justify-center transition-transform duration-150 group-hover:scale-105">
                    {/* Contested Bar */}
                    <div className="w-3 sm:w-4 flex flex-col justify-end h-full">
                      <div
                        style={{ height: `${Math.max(4, contestedHeightPct)}%` }}
                        className="w-full bg-emerald-500 hover:bg-emerald-400 rounded-t-sm transition-all duration-300 shadow-xs"
                        title={`Contested: ${contested}`}
                      />
                    </div>

                    {/* Liability Released Bar */}
                    <div className="w-3 sm:w-4 flex flex-col justify-end h-full">
                      <div
                        style={{ height: `${Math.max(4, acceptedHeightPct)}%` }}
                        className="w-full bg-rose-500 hover:bg-rose-400 rounded-t-sm transition-all duration-300 shadow-xs"
                        title={`Liability Released: ${accepted}`}
                      />
                    </div>
                  </div>

                  {/* X-axis Hour Label */}
                  <span className="mt-2 text-[11px] font-mono text-slate-500 group-hover:text-slate-900 group-hover:font-semibold transition-colors">
                    {item.hour}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-2 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
          <span className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />
            Direct Revenue Recovered: <strong className="text-[#172033] font-mono">{formatINR(metrics.directRevenueRecoveredINR)}</strong>
          </span>
          <span>
            Human Review Recovered: <strong className="text-[#172033] font-mono">{formatINR(metrics.humanReviewRecoveredINR)}</strong>
          </span>
        </div>
      </div>
    </div>
  );
}
