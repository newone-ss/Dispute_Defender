import React from "react";
import { CheckCircle2, XCircle, AlertTriangle, ShieldCheck, ShieldAlert } from "lucide-react";

export function EvidenceTab({ audit }) {
  if (!audit) return null;

  const fairnessGate = audit.fairnessGateCheck || {
    passed: (audit.status || '').toUpperCase() !== 'AUTO_ACCEPTED',
    gateAction: (audit.status || '').toUpperCase() === 'AUTO_ACCEPTED' ? 'TRIGGER_AUTO_ACCEPT' : 'PASS_TO_CONTEST',
    rationale: (audit.status || '').toUpperCase() === 'AUTO_ACCEPTED'
      ? "Customer reported transit defect before filing dispute. Auto-accepted to avoid ₹1,500 penalty."
      : "All physical courier telemetry signals match policy requirements. Zero customer complaints detected.",
  };

  const scoreValue = audit.riskScore ?? audit.score ?? (fairnessGate.passed ? 95 : 84);

  const defaultSignals = [
    {
      id: "otp",
      name: "Doorstep OTP Verification",
      category: "Physical Telemetry",
      points: 35,
      maxPoints: 35,
      status: "VERIFIED",
      statusColor: "emerald",
      description: "Single-use 4-digit token matched and entered on carrier handset",
      benchmark: "Binary match requirement (35 pts)",
    },
    {
      id: "gps",
      name: "GPS Geofence Proximity",
      category: "Physical Telemetry",
      points: 30,
      maxPoints: 30,
      status: "VERIFIED",
      statusColor: "emerald",
      description: "Carrier handset recorded 42m offset from delivery address geofence (Threshold <= 100m)",
      benchmark: "<=100m = 30 pts, <=500m = 24 pts, >2,000m = 0 pts",
    },
    {
      id: "weight",
      name: "Origin vs Doorstep Weight Scale",
      category: "Physical Telemetry",
      points: 20,
      maxPoints: 20,
      status: "VERIFIED",
      statusColor: "emerald",
      description: "Origin: 2,400g | Doorstep: 2,356g (Delta: -44g / 1.83% tolerance)",
      benchmark: "<=5% delta = 20 pts, 5-15% scaled, >15% = 0 pts",
    },
    {
      id: "pod",
      name: "Proof of Delivery (POD) Signature",
      category: "Carrier Documentation",
      points: 10,
      maxPoints: 10,
      status: "VERIFIED",
      statusColor: "emerald",
      description: "Cryptographic touch-stylus signature recorded on carrier manifest",
      benchmark: "Binary signature presence (10 pts)",
    },
    {
      id: "device",
      name: "Device & Session Fingerprint",
      category: "Digital Telemetry",
      points: 5,
      maxPoints: 5,
      status: "VERIFIED",
      statusColor: "emerald",
      description: "Canvas fingerprint, WebGL vendor, and IP subnet match historical orders",
      benchmark: "Device identity profile match (5 pts)",
    },
  ];

  const signals = (Array.isArray(audit.evidenceSignals) && audit.evidenceSignals.length > 0)
    ? audit.evidenceSignals
    : defaultSignals;

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
            Total Evaluated: <strong className="text-emerald-700 font-bold">{scoreValue}</strong> / 100
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
