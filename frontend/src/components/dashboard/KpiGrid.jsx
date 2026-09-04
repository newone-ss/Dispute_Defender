import React from "react";
import { formatINR } from "../../utils/formatters";
import { ShieldCheck, AlertOctagon, TrendingUp, Layers } from "lucide-react";

export function KpiGrid({ metrics }) {
  if (!metrics) return null;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* 1. Net INR Protected */}
      <div className="bg-white border border-slate-200/90 rounded-xl p-5 shadow-[0_4px_16px_rgba(15,23,42,0.05)] hover:shadow-[0_6px_20px_rgba(15,23,42,0.08)] transition-all group">
        <div className="flex items-center justify-between text-xs text-slate-500 mb-3">
          <span className="font-medium text-slate-600">Net INR Protected</span>
          <span className="p-1.5 rounded-lg bg-emerald-50 text-emerald-600 border border-emerald-200/80">
            <ShieldCheck className="w-3.5 h-3.5" />
          </span>
        </div>
        <div className="text-2xl font-bold font-mono text-[#172033] tracking-tight">
          {formatINR(metrics.netProtectedINR)}
        </div>
        <div className="mt-2.5 flex items-center gap-2 text-xs">
          <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-mono font-medium bg-emerald-50 text-emerald-700 border border-emerald-200/80">
            +{metrics.roiBoostPercentage}%
          </span>
          <span className="text-slate-500 text-[11px]">Effective ROI Boost</span>
        </div>
      </div>

      {/* 2. Bank Penalties Avoided */}
      <div className="bg-white border border-slate-200/90 rounded-xl p-5 shadow-[0_4px_16px_rgba(15,23,42,0.05)] hover:shadow-[0_6px_20px_rgba(15,23,42,0.08)] transition-all group">
        <div className="flex items-center justify-between text-xs text-slate-500 mb-3">
          <span className="font-medium text-slate-600">Bank Loss Penalties Avoided</span>
          <span className="p-1.5 rounded-lg bg-rose-50 text-rose-600 border border-rose-200/80">
            <AlertOctagon className="w-3.5 h-3.5" />
          </span>
        </div>
        <div className="text-2xl font-bold font-mono text-[#172033] tracking-tight">
          {formatINR(metrics.bankPenaltiesAvoidedINR)}
        </div>
        <div className="mt-2.5 flex items-center gap-2 text-xs">
          <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-mono font-medium bg-rose-50 text-rose-700 border border-rose-200/80">
            {metrics.penaltiesAvoidedCount} Claims
          </span>
          <span className="text-slate-500 text-[11px]">@ ₹1,500 / dispute avoided</span>
        </div>
      </div>

      {/* 3. Auto-Contest Win Rate */}
      <div className="bg-white border border-slate-200/90 rounded-xl p-5 shadow-[0_4px_16px_rgba(15,23,42,0.05)] hover:shadow-[0_6px_20px_rgba(15,23,42,0.08)] transition-all group">
        <div className="flex items-center justify-between text-xs text-slate-500 mb-3">
          <span className="font-medium text-slate-600">Auto-Contest Win Rate</span>
          <span className="p-1.5 rounded-lg bg-sky-50 text-sky-600 border border-sky-200/80">
            <TrendingUp className="w-3.5 h-3.5" />
          </span>
        </div>
        <div className="text-2xl font-bold font-mono text-[#172033] tracking-tight">
          {metrics.autoContestWinRate}%
        </div>
        <div className="mt-2.5 flex items-center gap-2 text-xs">
          <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-mono font-medium bg-sky-50 text-sky-700 border border-sky-200/80">
            UDIR Validated
          </span>
          <span className="text-slate-500 text-[11px]">NPCI arbitration benchmark</span>
        </div>
      </div>

      {/* 4. Disputes Processed */}
      <div className="bg-white border border-slate-200/90 rounded-xl p-5 shadow-[0_4px_16px_rgba(15,23,42,0.05)] hover:shadow-[0_6px_20px_rgba(15,23,42,0.08)] transition-all group">
        <div className="flex items-center justify-between text-xs text-slate-500 mb-3">
          <span className="font-medium text-slate-600">Total Processed</span>
          <span className="p-1.5 rounded-lg bg-slate-100 text-slate-600 border border-slate-200">
            <Layers className="w-3.5 h-3.5" />
          </span>
        </div>
        <div className="text-2xl font-bold font-mono text-[#172033] tracking-tight">
          {metrics.totalDisputesProcessed}
        </div>
        <div className="mt-2.5 flex items-center gap-1.5 text-xs text-slate-500">
          <span className="text-emerald-700 font-mono text-[11px] font-semibold">32 Contested</span>
          <span>•</span>
          <span className="text-amber-700 font-mono text-[11px] font-semibold">6 Review</span>
          <span>•</span>
          <span className="text-rose-700 font-mono text-[11px] font-semibold">12 Released</span>
        </div>
      </div>
    </div>
  );
}
