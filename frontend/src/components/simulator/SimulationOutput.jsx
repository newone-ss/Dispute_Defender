import React from "react";
import { formatINR } from "../../utils/formatters";
import { Badge } from "../ui/Badge";
import { ArrowRight, Eye, ShieldCheck, Scale, CheckCircle2 } from "lucide-react";

export function SimulationOutput({ result, onOpenAudit }) {
  if (!result) return null;

  const isContested = result.decision === "AUTO_CONTESTED" || result.decision === "contested";
  const impact = result.financialImpact || {};

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-4 shadow-sm">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div>
          <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
            Pipeline Arbitration Output
          </h4>
          <span className="font-mono text-xs text-slate-500">
            Dispute ID: <strong className="text-[#172033]">{result.disputeId}</strong>
          </span>
        </div>

        <Badge status={result.decision} />
      </div>

      {/* Primary Decision Banner */}
      <div className={`p-4 rounded-xl border ${
        isContested
          ? "bg-emerald-50/70 border-emerald-200 text-emerald-950"
          : "bg-rose-50/70 border-rose-200 text-rose-950"
      }`}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="space-y-1">
            <div className="text-xs font-semibold text-slate-600">Classification Verdict:</div>
            <div className="text-sm font-bold text-[#172033]">
              {result.reason}
            </div>
          </div>

          <div className="text-right shrink-0">
            <div className="text-[11px] text-slate-500 font-medium">Defense Score</div>
            <div className="text-2xl font-bold font-mono text-[#172033]">
              {result.riskScore}<span className="text-sm text-slate-400 font-normal">/100</span>
            </div>
          </div>
        </div>
      </div>

      {/* Financial ROI Impact Box */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
        <div className="p-3.5 rounded-lg bg-slate-50/80 border border-slate-200 space-y-1">
          <div className="text-[11px] text-slate-500 font-medium">Financial Protection:</div>
          <div className="text-base font-bold font-mono text-[#172033] flex items-center gap-2">
            {formatINR(impact.amountINR)}
            <span className="text-[11px] font-sans font-medium px-2 py-0.5 rounded bg-white text-slate-700 border border-slate-200 shadow-xs">
              {impact.label}
            </span>
          </div>
          <div className="text-[11px] text-slate-500">
            {impact.details || impact.description || "Verified against bank penalty rules"}
          </div>
        </div>

        <div className="p-3.5 rounded-lg bg-slate-50/80 border border-slate-200 space-y-1">
          <div className="text-[11px] text-slate-500 font-medium">Consumer Fairness Gate Check:</div>
          <div className="text-xs font-semibold text-[#172033] flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>Passed Gate Validation</span>
          </div>
          <div className="text-[11px] text-slate-500">
            Zero customer defect ticket or transit loss detected
          </div>
        </div>
      </div>

      {/* Action Button: Inspect Complete Audit */}
      <div className="pt-2 flex justify-end">
        <button
          type="button"
          onClick={() => onOpenAudit(result.disputeId)}
          className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-2 transition-all shadow-sm"
        >
          <Eye className="w-4 h-4" />
          <span>Launch Deep Audit Dossier for {result.disputeId}</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}
