import React, { useState } from "react";
import { overrideDispute } from "../../api/disputes";
import { CheckCircle2, AlertTriangle, Key } from "lucide-react";

export function OperatorOverride({ disputeId, currentStatus, onOverrideSuccess }) {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedAction, setSelectedAction] = useState("AUTO_CONTESTED");
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [feedback, setFeedback] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!notes.trim()) {
      alert("Please provide an audit note justifying the override.");
      return;
    }

    setLoading(true);
    try {
      const res = await overrideDispute(disputeId, {
        newStatus: selectedAction,
        previousStatus: currentStatus,
        notes: notes.trim(),
      });
      setFeedback(`Status updated to ${selectedAction}. Audit logged.`);
      if (onOverrideSuccess) onOverrideSuccess(res);
      setTimeout(() => {
        setIsOpen(false);
        setFeedback(null);
      }, 1500);
    } catch (err) {
      alert("Override failed: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) {
    return (
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className="px-3 py-1.5 rounded-lg bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 text-xs font-medium flex items-center gap-1.5 transition-colors shadow-xs"
      >
        <Key className="w-3.5 h-3.5 text-amber-600" />
        <span>Operator Manual Override</span>
      </button>
    );
  }

  return (
    <div className="p-4 rounded-xl bg-amber-50/50 border border-amber-200 space-y-3 mt-4 text-xs">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 font-semibold text-amber-900">
          <AlertTriangle className="w-4 h-4 text-amber-600" />
          <span>Manual Operator Override (Level 2 Officer)</span>
        </div>
        <button
          type="button"
          onClick={() => setIsOpen(false)}
          className="text-slate-500 hover:text-slate-800 text-xs"
        >
          Cancel
        </button>
      </div>

      <p className="text-slate-600 leading-relaxed">
        Manual overrides bypass deterministic scoring policies and must carry an immutable audit rationale logged under your operator key.
      </p>

      {feedback ? (
        <div className="p-2.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 flex items-center gap-2 font-medium">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>{feedback}</span>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-1.5 cursor-pointer text-slate-800">
              <input
                type="radio"
                name="overrideAction"
                value="AUTO_CONTESTED"
                checked={selectedAction === "AUTO_CONTESTED"}
                onChange={(e) => setSelectedAction(e.target.value)}
                className="text-emerald-600 focus:ring-emerald-500"
              />
              <span className="font-semibold text-emerald-800">Force Contest (AUTO_CONTESTED)</span>
            </label>

            <label className="flex items-center gap-1.5 cursor-pointer text-slate-800">
              <input
                type="radio"
                name="overrideAction"
                value="AUTO_ACCEPTED"
                checked={selectedAction === "AUTO_ACCEPTED"}
                onChange={(e) => setSelectedAction(e.target.value)}
                className="text-rose-600 focus:ring-rose-500"
              />
              <span className="font-semibold text-rose-800">Release Liability (AUTO_ACCEPTED)</span>
            </label>
          </div>

          <div>
            <label className="block text-[11px] text-slate-600 mb-1 font-medium">
              Required Audit Rationale / Justification Note:
            </label>
            <textarea
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g., Merchant verified manual customer signature on original courier dispatch manifest."
              className="w-full p-2.5 text-xs bg-white border border-slate-200 rounded-lg text-[#172033] placeholder-slate-400 focus:outline-none focus:border-slate-300 shadow-xs"
              required
            />
          </div>

          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="px-3 py-1.5 rounded-lg bg-white border border-slate-200 text-slate-600 hover:bg-slate-50 text-xs"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white font-semibold text-xs transition-colors shadow-xs"
            >
              {loading ? "Submitting Override..." : "Confirm & Sign Override"}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
