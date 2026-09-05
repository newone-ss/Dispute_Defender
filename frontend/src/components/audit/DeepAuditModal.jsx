import React, { useState, useEffect } from "react";
import { Modal } from "../ui/Modal";
import { Tabs } from "../ui/Tabs";
import { Badge } from "../ui/Badge";
import { formatINR } from "../../utils/formatters";
import { getAudit } from "../../api/audit";
import { EvidenceTab } from "./EvidenceTab";
import { TelemetryTab } from "./TelemetryTab";
import { OcrTab } from "./OcrTab";
import { CustomerRagTab } from "./CustomerRagTab";
import { RawJsonTab } from "./RawJsonTab";
import { UdirPacketTab } from "./UdirPacketTab";
import { OperatorOverride } from "./OperatorOverride";
import { 
  ShieldCheck, 
  Activity, 
  Scan, 
  MessageSquareText, 
  FileCode2, 
  FileCheck2,
  AlertCircle
} from "lucide-react";

export function DeepAuditModal({ disputeId, isOpen, onClose }) {
  const [activeTab, setActiveTab] = useState("evidence");
  const [audit, setAudit] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!disputeId || !isOpen) return;

    let isCurrent = true;
    setLoading(true);

    getAudit(disputeId)
      .then((data) => {
        if (isCurrent) setAudit(data);
      })
      .catch((err) => {
        console.error("Failed to load audit data:", err);
      })
      .finally(() => {
        if (isCurrent) setLoading(false);
      });

    return () => {
      isCurrent = false;
    };
  }, [disputeId, isOpen]);

  if (!isOpen) return null;

  const tabs = [
    { id: "evidence", label: "Evidence Breakdown", icon: ShieldCheck, badge: audit ? `${audit.riskScore ?? audit.score ?? 95}/100` : null },
    { id: "telemetry", label: "Courier Telemetry", icon: Activity },
    { id: "ocr", label: "Manifest OCR", icon: Scan },
    { id: "rag", label: "Customer RAG", icon: MessageSquareText },
    { id: "udir", label: "NPCI UDIR Packet", icon: FileCheck2 },
    { id: "raw", label: "Raw JSON", icon: FileCode2 },
  ];

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      size="2xl"
      title={
        audit ? (
          <div className="flex flex-wrap items-center gap-3">
            <span className="font-mono text-base font-bold text-[#172033]">
              {audit.disputeId || audit.razorpay_dispute_id || disputeId}
            </span>
            <span className="text-slate-300 font-normal">|</span>
            <span className="font-mono text-sm font-bold text-emerald-700">
              {formatINR(audit.amount ?? audit.amount_inr ?? 2499)}
            </span>
            <span className="text-slate-300 font-normal">|</span>
            <div className="flex items-center gap-1.5 font-mono text-xs text-slate-600">
              <span>Score:</span>
              <strong className="text-[#172033]">{audit.riskScore ?? audit.score ?? 95}</strong>/100
            </div>
            <Badge status={audit.status} size="sm" />
          </div>
        ) : (
          "Loading Dispute Audit..."
        )
      }
      subtitle={audit ? audit.decisionReason : "Retrieving courier telemetry & vector embeddings..."}
    >
      {loading ? (
        <div className="p-12 text-center text-xs font-mono text-slate-400 animate-pulse">
          Ingesting courier telemetry signals and generating cryptographic verification digest...
        </div>
      ) : audit ? (
        <div className="space-y-5">
          {/* Inspection Tabs */}
          <Tabs
            tabs={tabs}
            activeTab={activeTab}
            onChange={setActiveTab}
          />

          {/* Active Tab Content Area */}
          <div className="mt-2 min-h-[380px]">
            {activeTab === "evidence" && <EvidenceTab audit={audit} />}
            {activeTab === "telemetry" && <TelemetryTab audit={audit} />}
            {activeTab === "ocr" && <OcrTab audit={audit} />}
            {activeTab === "rag" && <CustomerRagTab audit={audit} />}
            {activeTab === "udir" && <UdirPacketTab audit={audit} />}
            {activeTab === "raw" && <RawJsonTab audit={audit} />}
          </div>

          {/* Operator Override Bar */}
          <div className="pt-3 border-t border-slate-200">
            <OperatorOverride
              disputeId={audit.disputeId}
              currentStatus={audit.status}
              onOverrideSuccess={(updated) => {
                setAudit((prev) => ({
                  ...prev,
                  status: updated.newStatus,
                  decisionReason: `Manual operator override applied: "${updated.operatorNotes}"`,
                }));
              }}
            />
          </div>
        </div>
      ) : (
        <div className="p-8 text-center text-rose-600 text-xs flex items-center justify-center gap-2">
          <AlertCircle className="w-4 h-4" />
          <span>Could not retrieve audit record. Please try again.</span>
        </div>
      )}
    </Modal>
  );
}
