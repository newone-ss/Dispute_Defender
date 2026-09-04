import React, { useState } from "react";
import { Copy, Check, Sparkles, FileSpreadsheet } from "lucide-react";

export function OcrTab({ audit }) {
  const [copied, setCopied] = useState(false);
  const [isExpanded, setIsExpanded] = useState(true);

  if (!audit || !audit.ocrData) return null;

  const ocr = audit.ocrData;
  const jsonString = JSON.stringify(ocr.rawExtractedFields, null, 2);

  const handleCopy = () => {
    navigator.clipboard.writeText(jsonString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-4">
      {/* OCR Engine Metadata */}
      <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-purple-600" />
          <span className="font-semibold text-[#172033]">Vision OCR Extraction Engine</span>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200 font-medium">
            {ocr.engine}
          </span>
        </div>

        <div className="flex items-center gap-3 text-[11px] font-mono text-slate-500">
          <span>Confidence: <strong className="text-emerald-700 font-semibold">{(ocr.scanConfidence * 100).toFixed(1)}%</strong></span>
          <span>Processed: {ocr.processedAt.split("T")[1].slice(0, 8)} IST</span>
        </div>
      </div>

      {/* Extracted Structured Field Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 text-xs">
        <div className="p-2.5 rounded-lg bg-white border border-slate-200/90 space-y-0.5 font-mono shadow-xs">
          <div className="text-slate-400 text-[10px]">AWB Waybill</div>
          <div className="text-[#172033] font-bold">{ocr.rawExtractedFields?.waybill_number}</div>
        </div>
        <div className="p-2.5 rounded-lg bg-white border border-slate-200/90 space-y-0.5 font-mono shadow-xs">
          <div className="text-slate-400 text-[10px]">Recipient Signee</div>
          <div className="text-[#172033] font-bold">{ocr.rawExtractedFields?.recipient_name}</div>
        </div>
        <div className="p-2.5 rounded-lg bg-white border border-slate-200/90 space-y-0.5 font-mono shadow-xs">
          <div className="text-slate-400 text-[10px]">Shipper Hub</div>
          <div className="text-[#172033] font-bold truncate">{ocr.rawExtractedFields?.shipper_name}</div>
        </div>
        <div className="p-2.5 rounded-lg bg-white border border-slate-200/90 space-y-0.5 font-mono shadow-xs">
          <div className="text-slate-400 text-[10px]">Manifest Weight</div>
          <div className="text-[#172033] font-bold">{ocr.rawExtractedFields?.actual_manifest_weight_kg} kg</div>
        </div>
        <div className="p-2.5 rounded-lg bg-white border border-slate-200/90 space-y-0.5 font-mono shadow-xs">
          <div className="text-slate-400 text-[10px]">OTP Matched Flag</div>
          <div className="text-emerald-700 font-bold">{ocr.rawExtractedFields?.otp_verified_flag === "Y" ? "Verified (Y)" : "No (N)"}</div>
        </div>
        <div className="p-2.5 rounded-lg bg-white border border-slate-200/90 space-y-0.5 font-mono shadow-xs">
          <div className="text-slate-400 text-[10px]">POD Status</div>
          <div className="text-[#172033] font-bold">{ocr.rawExtractedFields?.pod_status}</div>
        </div>
      </div>

      {/* JSON Viewer with Crisp Terminal Contrast */}
      <div className="rounded-xl border border-slate-800 bg-[#0c121e] overflow-hidden shadow-xs">
        <div className="px-4 py-2 bg-slate-900 border-b border-slate-800 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2 text-slate-300 font-mono text-[11px]">
            <FileSpreadsheet className="w-3.5 h-3.5 text-purple-400" />
            <span>Pydantic ManifestData Model Output</span>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-[11px] text-slate-400 hover:text-slate-200"
            >
              {isExpanded ? "Collapse" : "Expand"}
            </button>
            <button
              type="button"
              onClick={handleCopy}
              className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 flex items-center gap-1 text-[11px] font-mono transition-colors border border-slate-700"
            >
              {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              <span>{copied ? "Copied" : "Copy JSON"}</span>
            </button>
          </div>
        </div>

        {isExpanded && (
          <pre className="p-4 text-xs font-mono text-purple-300 overflow-x-auto leading-relaxed max-h-72">
            {jsonString}
          </pre>
        )}
      </div>
    </div>
  );
}
