import React from "react";
import { CheckCircle2, XCircle, AlertTriangle, ShieldCheck, ShieldAlert } from "lucide-react";

export function EvidenceTab({ audit }) {
  if (!audit) return null;

  const signals = audit.evidenceSignals || [];
  const fairnessGate = audit.fairnessGateCheck || {};

  return (
    <div className="space-y-5">
      {/* Consumer Fairness Gate Status Card */}
      <div className={`p-4 rounded-xl border ${
        fairnessGate.passed 
          ? "bg-emerald-50/80 border-emerald-200 text-emerald-900"
          : "bg-rose-50/80 border-rose-200 text-rose-900"
      }`}>
        <div className="flex items-start gap-3">
          <div className="mt-0.5">
            {fairnessGate.passed ? (
              <ShieldCheck className="w-5 h-5 text-emerald-600 shrink-0" />
            ) : (
              <ShieldAlert className="w-5 h-5 text-rose-600 shrink-0" />
            )}
          </div>
          <div className="flex-1 text-xs">
            <div className="flex items-center justify-between font-semibold">
              <span className="text-sm">
                Consumer Fairness Gate: {fairnessGate.passed ? "PASSED (Clean Contest Eligibility)" : "TRIPPED (Zero-Liability Auto-Accept)"}
              </span>
              <span className="font-mono px-2 py-0.5 rounded text-[10px] bg-white border border-slate-200 text-slate-700 shadow-xs">
                {fairnessGate.gateAction}
              </span>
            </div>
            <p className="mt-1 text-slate-700 leading-relaxed">
              {fairnessGate.rationale}
            </p>
            {fairnessGate.defectTicketId && (
              <div className="mt-2 font-mono text-[11px] text-amber-800 bg-amber-100/70 px-2.5 py-1 rounded inline-block border border-amber-200">
                Prior Support Ticket Detected: {fairnessGate.defectTicketId} (Pre-Dispute Defect Report)
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 5-Signal Mathematical Telemetry Scorecard */}
      <div className="space-y-2.5">
        <div className="flex items-center justify-between text-xs text-slate-500 px-1">
          <span className="font-semibold uppercase tracking-wider text-[11px]">
            Mathematical Signal Breakdown (100 Pts Policy)
          </span>
          <span className="font-mono text-slate-600">
            Total Evaluated: <strong className="text-emerald-700 font-bold">{audit.riskScore}</strong> / 100
          </span>
        </div>

        <div className="space-y-2">
          {signals.map((sig) => {
            const isVerified = sig.status === "VERIFIED";
            const isAmbiguous = sig.status === "AMBIGUOUS";

            return (
              <div
                key={sig.id}
                className="p-3.5 rounded-lg bg-slate-50/70 border border-slate-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-white hover:shadow-xs transition-all"
              >
                <div className="flex items-start gap-3">
                  <div className="mt-0.5">
                    {isVerified ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                    ) : isAmbiguous ? (
                      <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                    ) : (
                      <XCircle className="w-4 h-4 text-rose-600 shrink-0" />
                    )}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold text-[#172033]">
                        {sig.name}
                      </span>
                      <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-white border border-slate-200 text-slate-600">
                        {sig.category}
                      </span>
                    </div>
                    <p className="text-xs text-slate-600 mt-0.5">
                      {sig.description}
                    </p>
                    <div className="text-[10px] text-slate-500 font-mono mt-1">
                      Rule: {sig.benchmark}
                    </div>
                  </div>
                </div>

                <div className="sm:text-right shrink-0">
                  <div className="flex sm:flex-col items-center sm:items-end justify-between gap-1">
                    <span className={`font-mono text-sm font-bold ${
                      sig.points > 0 ? "text-emerald-700" : "text-slate-400"
                    }`}>
                      +{sig.points} <span className="text-slate-500 text-xs font-normal">/ {sig.maxPoints} pts</span>
                    </span>
                    <span className={`text-[10px] font-mono font-medium px-2 py-0.5 rounded ${
                      isVerified
                        ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                        : isAmbiguous
                        ? "bg-amber-50 text-amber-700 border border-amber-200"
                        : "bg-rose-50 text-rose-700 border border-rose-200"
                    }`}>
                      {sig.status}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
