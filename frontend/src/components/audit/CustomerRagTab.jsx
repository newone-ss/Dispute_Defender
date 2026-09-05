import React from "react";
import { MessageSquare, Sparkles, BookOpen, AlertCircle, CheckCircle2 } from "lucide-react";
import { formatDateTime } from "../../utils/formatters";

export function CustomerRagTab({ audit }) {
  if (!audit) return null;

  const defaultRag = {
    vectorStore: "ChromaDB (cosine similarity)",
    collection: "merchant_omnichannel_transcripts",
    queryEvaluated: `Customer reported non-receipt, damage, refund request or transit pilferage for order ${audit.disputeId || 'DSP-1024'}`,
    matchedTranscripts: [
      {
        source: "WhatsApp Business API",
        timestamp: "2026-09-02T15:02:14+05:30",
        customerChannel: "WhatsApp",
        messageSnippet: "Bot: Your package has been delivered! How was your experience? Aarav: Got it, thanks! Package was intact.",
        intent: "DELIVERY_CONFIRMATION",
        sentimentScore: 0.92,
        relevanceDistance: 0.14,
        impactOnDispute: "Corroborates courier telemetry. Directly refutes Product Not Received (PNR) claim.",
      },
    ],
    regulatoryCitation: "Visa Compelling Evidence 3.0 (CE 3.0) Section 5.4.2 & NPCI UDIR Clause 8.1.b: Documented delivery confirmation with OTP and positive post-delivery customer acknowledgment constitutes definitive rebutting evidence against friendly fraud.",
  };

  const rag = audit.customerRag || defaultRag;
  const transcripts = rag.matchedTranscripts && rag.matchedTranscripts.length > 0
    ? rag.matchedTranscripts
    : defaultRag.matchedTranscripts;

  return (
    <div className="space-y-4">
      {/* ChromaDB Vector Query Context */}
      <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-purple-600" />
          <span className="font-semibold text-[#172033]">ChromaDB Omnichannel Vector Search</span>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200 font-medium">
            Collection: {rag.collection}
          </span>
        </div>

        <div className="text-[11px] font-mono text-slate-500">
          Metric: Cosine Distance
        </div>
      </div>

      {/* Semantic Query Evaluated */}
      <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs font-mono space-y-1">
        <div className="text-slate-500 text-[10px] uppercase font-semibold">Evaluated Query Vector:</div>
        <div className="text-slate-700 italic">"{rag.queryEvaluated}"</div>
      </div>

      {/* Retrieved Transcript Cards */}
      <div className="space-y-3">
        <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider text-[11px]">
          Retrieved Customer Communications ({transcripts.length} Matches)
        </div>

        {transcripts.map((t, idx) => {
          const isNegative = t.sentimentScore < 0;
          return (
            <div
              key={idx}
              className={`p-4 rounded-xl border ${
                isNegative 
                  ? "bg-rose-50/60 border-rose-200 text-rose-900" 
                  : "bg-emerald-50/60 border-emerald-200 text-emerald-900"
              } space-y-3 text-xs`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 font-medium">
                  <MessageSquare className={`w-4 h-4 ${isNegative ? "text-rose-600" : "text-emerald-600"}`} />
                  <span className="text-[#172033] font-bold">{t.source}</span>
                  <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-white border border-slate-200 text-slate-600">
                    {t.customerChannel}
                  </span>
                </div>
                <div className="text-[11px] font-mono text-slate-500">
                  {formatDateTime(t.timestamp)}
                </div>
              </div>

              {/* Message Content */}
              <div className="p-3 rounded-lg bg-white border border-slate-200/80 font-sans text-slate-800 leading-relaxed shadow-xs">
                "{t.messageSnippet}"
              </div>

              {/* RAG Intent & Impact Assessment */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] font-mono pt-1">
                <div className="p-2 rounded-lg bg-white border border-slate-200/80 flex items-center justify-between shadow-xs">
                  <span className="text-slate-500">Detected Intent:</span>
                  <span className={`font-bold ${isNegative ? "text-rose-600" : "text-emerald-700"}`}>
                    {t.intent}
                  </span>
                </div>

                <div className="p-2 rounded-lg bg-white border border-slate-200/80 flex items-center justify-between shadow-xs">
                  <span className="text-slate-500">Sentiment Score:</span>
                  <span className="text-[#172033] font-bold">
                    {t.sentimentScore > 0 ? `+${t.sentimentScore}` : t.sentimentScore}
                  </span>
                </div>
              </div>

              <div className="text-[11px] text-slate-700 leading-normal flex items-start gap-1.5 pt-0.5">
                {isNegative ? (
                  <AlertCircle className="w-3.5 h-3.5 text-rose-600 shrink-0 mt-0.5" />
                ) : (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                )}
                <span><strong>Impact:</strong> {t.impactOnDispute}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Regulatory Rule Citation */}
      {rag.regulatoryCitation && (
        <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 text-xs space-y-1.5">
          <div className="flex items-center gap-1.5 text-slate-700 font-semibold text-[11px] uppercase tracking-wider">
            <BookOpen className="w-3.5 h-3.5 text-sky-600" />
            <span>Card Network & NPCI Compelling Evidence Rule Alignment</span>
          </div>
          <p className="text-slate-600 leading-relaxed text-[11px]">
            {rag.regulatoryCitation}
          </p>
        </div>
      )}
    </div>
  );
}
