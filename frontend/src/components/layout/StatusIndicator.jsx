import React from "react";
import { Activity, ShieldCheck, Wifi } from "lucide-react";

export function StatusIndicator({ status = "live", className = "" }) {
  const statusConfigs = {
    live: {
      text: "Gateway Connected",
      subtext: "Sub-25ms Ingestion Active",
      dotClass: "bg-emerald-400 animate-pulse",
      badgeClass: "text-emerald-400 bg-emerald-950/40 border-emerald-800/40",
    },
    fallback: {
      text: "Standalone Mode",
      subtext: "Synthetic Telemetry Active",
      dotClass: "bg-sky-400",
      badgeClass: "text-sky-400 bg-sky-950/40 border-sky-800/40",
    },
    connecting: {
      text: "Connecting...",
      subtext: "Checking daemon lease",
      dotClass: "bg-amber-400 animate-ping",
      badgeClass: "text-amber-400 bg-amber-950/40 border-amber-800/40",
    },
  }[status] || {
    text: "Operational",
    subtext: "Ready",
    dotClass: "bg-emerald-400",
    badgeClass: "text-emerald-400 bg-emerald-950/40 border-emerald-800/40",
  };

  return (
    <div className={`inline-flex items-center gap-2 px-2.5 py-1 rounded-full border text-xs ${statusConfigs.badgeClass} ${className}`}>
      <span className={`w-2 h-2 rounded-full ${statusConfigs.dotClass}`} />
      <div className="flex items-center gap-1.5 font-medium">
        <span>{statusConfigs.text}</span>
        <span className="text-[10px] opacity-70 hidden sm:inline">({statusConfigs.subtext})</span>
      </div>
    </div>
  );
}
