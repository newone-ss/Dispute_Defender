import React from "react";
import type { Metrics } from "../lib/api";

interface MetricCardsProps {
  metrics: Metrics | null;
  loading?: boolean;
}

export const MetricCards: React.FC<MetricCardsProps> = ({ metrics, loading }) => {
  if (loading || !metrics) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="glass-card rounded-xl p-5 border border-slate-800 animate-pulse">
            <div className="h-4 bg-slate-800 rounded w-1/2 mb-3" />
            <div className="h-8 bg-slate-800 rounded w-3/4 mb-2" />
            <div className="h-3 bg-slate-800 rounded w-1/3" />
          </div>
        ))}
      </div>
    );
  }

  const formatINR = (val: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(val);
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
      {/* 1. Net INR Saved */}
      <div className="glass-card rounded-xl p-5 border border-slate-800/80 relative overflow-hidden group">
        <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-blue-500 to-indigo-600" />
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider">Net INR Saved</span>
          <span className="p-2 rounded-lg bg-blue-500/10 text-blue-400 text-lg">💰</span>
        </div>
        <div className="text-2xl font-bold text-white tracking-tight">
          {formatINR(metrics.net_inr_saved)}
        </div>
        <div className="flex items-center gap-1.5 mt-2 text-xs text-emerald-400">
          <span>↑</span>
          <span>Defended via NPCI UDIR evidence</span>
        </div>
      </div>

      {/* 2. Bank Penalties Avoided */}
      <div className="glass-card rounded-xl p-5 border border-slate-800/80 relative overflow-hidden group">
        <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-emerald-500 to-teal-600" />
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider">Penalties Avoided</span>
          <span className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 text-lg">🛡️</span>
        </div>
        <div className="text-2xl font-bold text-emerald-300 tracking-tight">
          {formatINR(metrics.bank_penalties_avoided)}
        </div>
        <div className="flex items-center gap-1.5 mt-2 text-xs text-slate-400">
          <span>₹1,500/case saved via Fairness Gate</span>
        </div>
      </div>

      {/* 3. Auto Win Rate */}
      <div className="glass-card rounded-xl p-5 border border-slate-800/80 relative overflow-hidden group">
        <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-purple-500 to-pink-600" />
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider">Auto-Contest Win Rate</span>
          <span className="p-2 rounded-lg bg-purple-500/10 text-purple-400 text-lg">🎯</span>
        </div>
        <div className="text-2xl font-bold text-white tracking-tight">
          {metrics.auto_win_rate.toFixed(1)}%
        </div>
        <div className="flex items-center gap-1.5 mt-2 text-xs text-purple-300">
          <span>{metrics.auto_contested_count} automated representments</span>
        </div>
      </div>

      {/* 4. Total Ingested Disputes */}
      <div className="glass-card rounded-xl p-5 border border-slate-800/80 relative overflow-hidden group">
        <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-amber-500 to-orange-600" />
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider">Disputes Intercepted</span>
          <span className="p-2 rounded-lg bg-amber-500/10 text-amber-400 text-lg">⚡</span>
        </div>
        <div className="text-2xl font-bold text-white tracking-tight">
          {metrics.total_disputes}
        </div>
        <div className="flex items-center gap-2 mt-2 text-xs">
          <span className="text-amber-400 font-medium">{metrics.needs_review_count} need review</span>
          <span className="text-slate-500">•</span>
          <span className="text-rose-400 font-medium">{metrics.auto_accepted_count} auto-accepted</span>
        </div>
      </div>
    </div>
  );
};
