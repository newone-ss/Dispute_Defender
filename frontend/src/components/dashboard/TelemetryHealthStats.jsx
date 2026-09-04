import React from "react";
import { KeyRound, Navigation, Scale, FileCheck, PackageCheck } from "lucide-react";

export function TelemetryHealthStats({ compliance }) {
  if (!compliance) return null;

  const items = [
    {
      label: "Doorstep OTP Match",
      value: compliance.otpVerificationRate,
      icon: KeyRound,
      color: "emerald",
      detail: "Verified customer 4-digit token",
    },
    {
      label: "GPS Proximity <= 100m",
      value: compliance.gpsGeofenceCompliance,
      icon: Navigation,
      color: "sky",
      detail: "Handset coordinates within geofence",
    },
    {
      label: "Weight Delta <= 5%",
      value: compliance.weightScaleMatchRate,
      icon: Scale,
      color: "emerald",
      detail: "Transit scale reconciliation",
    },
    {
      label: "POD Digital Signature",
      value: compliance.podSignatureMatchRate,
      icon: FileCheck,
      color: "sky",
      detail: "Legible recipient confirmation",
    },
    {
      label: "Open Box Delivery (OBD)",
      value: compliance.obdProtocolRate,
      icon: PackageCheck,
      color: "purple",
      detail: "Doorstep unbox verification",
    },
  ];

  return (
    <div className="bg-white border border-slate-200/90 rounded-xl p-5 shadow-[0_2px_8px_rgba(15,23,42,0.04)]">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Courier Telemetry Verification Integrity
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Physical evidence signals captured across Indian courier networks (BlueDart, Delhivery, Shadowfax)
          </p>
        </div>
        <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200 font-medium">
          50 Ground-Truth Samples
        </span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <div
              key={item.label}
              className="p-3.5 rounded-lg bg-slate-50/80 border border-slate-200/80 space-y-2 hover:bg-white hover:shadow-xs transition-all"
            >
              <div className="flex items-center justify-between text-slate-500">
                <span className="text-xs font-medium text-slate-700 truncate">{item.label}</span>
                <Icon className="w-4 h-4 shrink-0 text-slate-400" />
              </div>

              <div className="flex items-baseline gap-2">
                <span className="text-xl font-bold font-mono text-[#172033]">{item.value}%</span>
                <span className="text-[10px] text-slate-500 font-mono">passed</span>
              </div>

              {/* Progress bar */}
              <div className="h-1.5 w-full bg-slate-200/80 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${
                    item.color === "emerald" 
                      ? "bg-emerald-600" 
                      : item.color === "sky"
                      ? "bg-sky-600"
                      : "bg-purple-600"
                  }`}
                  style={{ width: `${item.value}%` }}
                />
              </div>

              <p className="text-[11px] text-slate-500 truncate">{item.detail}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
