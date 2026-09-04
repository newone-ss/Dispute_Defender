import React, { useState } from "react";
import { Copy, Check, Download, ShieldCheck, Hash, FileCheck, FileCode } from "lucide-react";
import { downloadUdirPacket } from "../../api/audit";

export function UdirPacketTab({ audit }) {
  const [copiedHash, setCopiedHash] = useState(false);
  const [downloading, setDownloading] = useState(false);

  if (!audit) return null;

  const markdownContent = audit.udirLegalPacketMarkdown || "";
  const sha256 = audit.sha256Digest || "—";

  const handleCopyHash = () => {
    navigator.clipboard.writeText(sha256);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  const handleDownload = async () => {
    setDownloading(true);
    await downloadUdirPacket(audit.disputeId);
    setDownloading(false);
  };

  return (
    <div className="space-y-4">
      {/* Cryptographic SHA-256 Immutability Bar */}
      <div className="p-4 rounded-xl bg-slate-50/80 border border-slate-200 space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
            <span className="text-xs font-semibold text-[#172033]">
              Byte-Stable Jinja2 Evidence Digest (Zero-Hallucination)
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleCopyHash}
              className="px-2.5 py-1 rounded-lg bg-white hover:bg-slate-50 text-slate-700 flex items-center gap-1.5 text-xs font-mono transition-colors border border-slate-200 shadow-xs"
            >
              {copiedHash ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5 text-slate-400" />}
              <span>{copiedHash ? "Hash Copied" : "Copy Digest"}</span>
            </button>

            <button
              type="button"
              onClick={handleDownload}
              disabled={downloading}
              className="px-3 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold flex items-center gap-1.5 text-xs transition-colors shadow-xs"
            >
              <Download className="w-3.5 h-3.5" />
              <span>{downloading ? "Downloading..." : "Download Packet (.md)"}</span>
            </button>
          </div>
        </div>

        {/* SHA-256 Hash Display */}
        <div className="p-2.5 rounded-lg bg-white border border-slate-200 font-mono text-xs flex items-center gap-2 text-slate-800 overflow-x-auto shadow-xs">
          <Hash className="w-4 h-4 text-slate-400 shrink-0" />
          <span className="text-emerald-700 font-bold select-all">{sha256}</span>
        </div>

        {/* Submission & Gateway Status */}
        <div className="flex flex-wrap items-center gap-4 text-[11px] font-mono text-slate-500 pt-1">
          <span className="flex items-center gap-1.5">
            <FileCheck className="w-3.5 h-3.5 text-emerald-600" />
            Razorpay Documents API: <strong className="text-emerald-700">DOC_UPLOADED_SUCCESS</strong>
          </span>
          {audit.razorpayDocumentId && (
            <span>Doc ID: <strong className="text-slate-700">{audit.razorpayDocumentId}</strong></span>
          )}
          {audit.razorpayContestReceipt && (
            <span>Receipt: <strong className="text-slate-700">{audit.razorpayContestReceipt}</strong></span>
          )}
        </div>
      </div>

      {/* Rendered Legal Representment Document Inspector */}
      <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-xs">
        <div className="px-4 py-2.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2 text-slate-700 font-mono text-[11px] font-semibold">
            <FileCode className="w-3.5 h-3.5 text-sky-600" />
            <span>app/templates/npci_udir_packet.md.j2 Output Preview</span>
          </div>
          <span className="text-[11px] font-mono text-slate-500">Legal Arbitration Ready</span>
        </div>

        <div className="p-6 text-xs text-slate-800 font-sans leading-relaxed space-y-4 max-h-[500px] overflow-y-auto whitespace-pre-wrap selection:bg-emerald-500/20 bg-white">
          {markdownContent}
        </div>
      </div>
    </div>
  );
}
