import React from "react";
import { formatDistance } from "../../utils/formatters";

export function OtpPill({ verified }) {
  if (verified) {
    return (
      <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[11px] font-mono bg-emerald-50 text-emerald-700 border border-emerald-200/90 font-medium">
        ✓ OTP
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[11px] font-mono bg-rose-50 text-rose-700 border border-rose-200/90 font-medium">
      ✗ No OTP
    </span>
  );
}

export function GpsPill({ distanceMeters }) {
  const isClose = distanceMeters <= 100;
  const isModerate = distanceMeters <= 500;

  let colorClass = "bg-emerald-50 text-emerald-700 border-emerald-200/90";
  if (!isClose && isModerate) {
    colorClass = "bg-amber-50 text-amber-700 border-amber-200/90";
  } else if (!isClose && !isModerate) {
    colorClass = "bg-rose-50 text-rose-700 border-rose-200/90";
  }

  return (
    <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[11px] font-mono border font-medium ${colorClass}`}>
      {formatDistance(distanceMeters)}
    </span>
  );
}

export function WeightPill({ deltaPct, originGrams, doorstepGrams }) {
  const deltaGrams = originGrams && doorstepGrams ? originGrams - doorstepGrams : null;
  const isExcessive = deltaGrams !== null && deltaGrams > 100;
  const isGood = deltaPct <= 5;

  let colorClass = "bg-emerald-50 text-emerald-700 border-emerald-200/90";
  if (isExcessive) {
    colorClass = "bg-rose-50 text-rose-700 border-rose-200/90";
  } else if (!isGood) {
    colorClass = "bg-amber-50 text-amber-700 border-amber-200/90";
  }

  return (
    <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[11px] font-mono border font-medium ${colorClass}`}>
      Δ {deltaPct}%
    </span>
  );
}

export function PodPill({ verified }) {
  if (verified) {
    return (
      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-mono bg-sky-50 text-sky-700 border border-sky-200/90 font-medium">
        ✓ POD
      </span>
    );
  }
  return (
    <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-mono bg-slate-100 text-slate-400 border border-slate-200">
      —
    </span>
  );
}

export function ObdPill({ hasObd }) {
  if (!hasObd) return null;
  return (
    <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold bg-purple-50 text-purple-700 border border-purple-200/90">
      OBD
    </span>
  );
}
