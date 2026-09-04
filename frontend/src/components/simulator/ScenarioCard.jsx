import React from "react";
import { ShieldCheck, AlertOctagon, Scale, Box, AlertTriangle, Check } from "lucide-react";

export function ScenarioCard({ scenario, isSelected, isRunning, onSelect }) {
  const isContested = scenario.expectedDecision === "AUTO_CONTESTED";

  const getIcon = () => {
    switch (scenario.id) {
      case "winnable_clean":
        return <ShieldCheck className="w-4 h-4 text-emerald-600" />;
      case "customer_defect_ticket":
        return <AlertOctagon className="w-4 h-4 text-rose-600" />;
      case "transit_weight_loss":
        return <Scale className="w-4 h-4 text-amber-600" />;
      case "obd_clean":
        return <Box className="w-4 h-4 text-emerald-600" />;
      case "fraud_no_otp":
        return <AlertTriangle className="w-4 h-4 text-rose-600" />;
      default:
        return <ShieldCheck className="w-4 h-4 text-emerald-600" />;
    }
  };

  return (
    <div
      onClick={onSelect}
      className={`p-4 rounded-xl border transition-all duration-200 cursor-pointer flex flex-col justify-between relative ${
        isSelected
          ? "bg-white border-emerald-500 shadow-md ring-2 ring-emerald-500/20"
          : "bg-white border-slate-200 hover:border-slate-300 hover:shadow-sm"
      }`}
    >
      <div className="space-y-2.5">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-slate-50 border border-slate-200">
              {getIcon()}
            </div>
            <div>
              <h3 className="text-xs font-bold text-[#172033] leading-snug">
                {scenario.title}
              </h3>
              <p className="text-[11px] text-slate-500 font-medium">
                {scenario.subtitle}
              </p>
            </div>
          </div>

          <span
            className={`text-[10px] font-semibold px-2 py-0.5 rounded-full shrink-0 border ${
              isContested
                ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                : "bg-rose-50 text-rose-700 border-rose-200"
            }`}
          >
            {isContested ? "Auto Contested" : "Auto Accepted"}
          </span>
        </div>

        <p className="text-xs text-slate-600 leading-relaxed pt-1">
          {scenario.description}
        </p>
      </div>

      <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
        <div className="flex items-center gap-1.5 text-[11px] text-slate-500 font-medium">
          <span className="text-slate-400">Signal:</span>
          <span className="text-slate-700 font-semibold">{scenario.riskSignal}</span>
        </div>

        {isSelected && (
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
            <Check className="w-3 h-3" /> Selected
          </span>
        )}
      </div>
    </div>
  );
}
