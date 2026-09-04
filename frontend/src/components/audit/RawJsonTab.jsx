import React, { useState } from "react";
import { Copy, Check, Terminal } from "lucide-react";

export function RawJsonTab({ audit }) {
  const [copied, setCopied] = useState(false);

  if (!audit) return null;

  const rawJson = JSON.stringify(audit.rawDatabaseRecord || audit, null, 2);

  const handleCopy = () => {
    navigator.clipboard.writeText(rawJson);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between text-xs text-slate-500">
        <div className="flex items-center gap-2 font-mono text-[11px]">
          <Terminal className="w-3.5 h-3.5 text-slate-500" />
          <span>Disputes & AuditJobs SQLite Row Representation</span>
        </div>
        <button
          type="button"
          onClick={handleCopy}
          className="px-3 py-1.5 rounded-lg bg-white hover:bg-slate-50 text-slate-700 flex items-center gap-1.5 text-xs font-mono transition-colors border border-slate-200 shadow-xs"
        >
          {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5 text-slate-500" />}
          <span>{copied ? "Copied to Clipboard" : "Copy Raw JSON"}</span>
        </button>
      </div>

      <div className="rounded-xl border border-slate-800 bg-[#0c121e] p-4 overflow-hidden shadow-xs">
        <pre className="text-xs font-mono text-slate-200 leading-relaxed overflow-x-auto max-h-[500px]">
          {rawJson}
        </pre>
      </div>
    </div>
  );
}
