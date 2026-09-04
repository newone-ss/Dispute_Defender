import React from "react";
import { CheckCircle2, Loader2, Circle, Clock } from "lucide-react";

export function PipelineProgress({ currentStepIndex, isRunning, pipelineSteps = [] }) {
  const defaultSteps = [
    { name: "Webhook Ingestion", detail: "POST /api/webhook committed in sub-25ms" },
    { name: "Signature Verification", detail: "HMAC-SHA256 signature timing-safe validation" },
    { name: "Durable Queue Lease", detail: "Dispute lease acquired by audit queue worker" },
    { name: "Courier Telemetry Audit", detail: "Doorstep OTP, GPS geofence & scale weight check" },
    { name: "Evidence RAG Extraction", detail: "ChromaDB support ticket search & manifest OCR" },
    { name: "Consumer Fairness Gate", detail: "Zero-liability defect ticket check to avoid ₹1,500 penalty" },
    { name: "NPCI Legal Packet Compilation", detail: "Deterministic routing & Jinja2 UDIR brief generated" },
  ];

  const stepsToRender = pipelineSteps.length > 0 ? pipelineSteps : defaultSteps;

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-4 shadow-sm">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div>
          <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
            Defense Pipeline Progression
          </h4>
          <p className="text-[11px] text-slate-500 mt-0.5">
            Real-time deterministic audit execution steps
          </p>
        </div>
        <div className="text-[11px] font-mono">
          {isRunning ? (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-50 text-amber-700 border border-amber-200 font-medium">
              <Loader2 className="w-3.5 h-3.5 animate-spin" /> In-Flight Execution
            </span>
          ) : currentStepIndex >= stepsToRender.length - 1 ? (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-semibold">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Pipeline Complete
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-50 text-slate-600 border border-slate-200">
              <Clock className="w-3 h-3 text-slate-400" /> Ready for Dispatch
            </span>
          )}
        </div>
      </div>

      <div className="space-y-2">
        {stepsToRender.map((step, idx) => {
          const isDone = currentStepIndex > idx || (currentStepIndex === stepsToRender.length - 1 && !isRunning);
          const isCurrent = currentStepIndex === idx && isRunning;

          return (
            <div
              key={idx}
              className={`p-3 rounded-lg flex items-center justify-between gap-3 text-xs transition-all duration-200 ${
                isCurrent
                  ? "bg-emerald-50 border border-emerald-200 text-emerald-900 shadow-xs"
                  : isDone
                  ? "bg-slate-50/80 text-slate-700 border border-slate-200/60"
                  : "bg-white text-slate-400 opacity-60 border border-transparent"
              }`}
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className="shrink-0 flex items-center justify-center w-5 h-5">
                  {isDone ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  ) : isCurrent ? (
                    <Loader2 className="w-4 h-4 text-emerald-600 animate-spin" />
                  ) : (
                    <Circle className="w-3.5 h-3.5 text-slate-300" />
                  )}
                </div>

                <div className="truncate">
                  <div className={`font-semibold ${isCurrent ? "text-emerald-900" : isDone ? "text-[#172033]" : "text-slate-400"}`}>
                    {step.step || step.name}
                  </div>
                  <div className="text-[11px] text-slate-500 truncate mt-0.5">
                    {step.detail}
                  </div>
                </div>
              </div>

              {step.durationMs !== undefined && isDone && (
                <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-white border border-slate-200 text-slate-500 shrink-0 shadow-xs">
                  +{step.durationMs}ms
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
