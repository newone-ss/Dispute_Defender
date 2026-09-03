import React from "react";

interface TelemetryBadgeProps {
  type: "otp" | "geofence" | "weight" | "defect" | "status";
  value?: any;
  className?: string;
}

export const TelemetryBadge: React.FC<TelemetryBadgeProps> = ({
  type,
  value,
  className = "",
}) => {
  if (type === "status") {
    const status = String(value || "RECEIVED");
    switch (status) {
      case "AUTO_CONTESTED":
      case "WON":
        return (
          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 ${className}`}>
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            AUTO CONTESTED
          </span>
        );
      case "NEEDS_REVIEW":
        return (
          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-amber-500/15 text-amber-400 border border-amber-500/30 ${className}`}>
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
            NEEDS REVIEW
          </span>
        );
      case "AUTO_ACCEPTED":
        return (
          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-rose-500/15 text-rose-400 border border-rose-500/30 ${className}`}>
            <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
            AUTO ACCEPTED
          </span>
        );
      case "MANUALLY_CONTESTED":
        return (
          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-sky-500/15 text-sky-400 border border-sky-500/30 ${className}`}>
            <span className="w-1.5 h-1.5 rounded-full bg-sky-400" />
            MANUAL OVERRIDE
          </span>
        );
      default:
        return (
          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700 ${className}`}>
            <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
            {status}
          </span>
        );
    }
  }

  if (type === "otp") {
    const isVerified = Boolean(value);
    return isVerified ? (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-950/80 text-emerald-300 border border-emerald-700/50" title="Delivery OTP physically verified">
        <span>✅</span> OTP Verified
      </span>
    ) : (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-slate-900 text-slate-400 border border-slate-800" title="No OTP confirmation">
        <span>❌</span> No OTP
      </span>
    );
  }

  if (type === "geofence") {
    const dist = typeof value === "number" ? value : null;
    if (dist === null) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-slate-900 text-slate-400 border border-slate-800">
          📍 GPS: N/A
        </span>
      );
    }
    const isClose = dist <= 5.0;
    const isMedium = dist <= 15.0;
    return (
      <span
        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium border ${
          isClose
            ? "bg-emerald-950/70 text-emerald-300 border-emerald-700/50"
            : isMedium
            ? "bg-amber-950/70 text-amber-300 border-amber-700/50"
            : "bg-rose-950/70 text-rose-300 border-rose-700/50"
        }`}
        title={`Delivery coordinate distance from billing address: ${dist} km`}
      >
        <span>📍</span> {dist.toFixed(1)} km
      </span>
    );
  }

  if (type === "weight") {
    const loss = typeof value === "number" ? value : 0;
    const isLossHeavy = loss > 100;
    return isLossHeavy ? (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-rose-950/80 text-rose-300 border border-rose-700/60" title={`Transit weight loss: ${loss}g (>100g gate)`}>
        <span>⚠️</span> -{loss}g Loss
      </span>
    ) : (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-950/60 text-emerald-300 border border-emerald-800/40" title="Origin-to-doorstep weight intact">
        <span>⚖️</span> Weight OK
      </span>
    );
  }

  if (type === "defect") {
    const isDefect = Boolean(value);
    if (!isDefect) return null;
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-indigo-950/80 text-indigo-300 border border-indigo-700/60" title="Open customer defect support ticket active">
        <span>🎫</span> Support Ticket Open
      </span>
    );
  }

  return null;
};
