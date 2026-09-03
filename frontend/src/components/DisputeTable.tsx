import { useState } from "react";
import type { Dispute } from "../lib/api";
import { manualOverride } from "../lib/api";

interface Props {
  disputes: Dispute[];
  onRefresh: () => void;
}

const STATUS_STYLES: Record<
  string,
  { bg: string; text: string; border: string; label: string }
> = {
  RECEIVED: {
    bg: "rgba(100,116,139,0.15)",
    text: "#94a3b8",
    border: "rgba(100,116,139,0.3)",
    label: "Received",
  },
  PROCESSING: {
    bg: "rgba(82,143,240,0.15)",
    text: "#6ea8ff",
    border: "rgba(82,143,240,0.3)",
    label: "Processing",
  },
  AUTO_CONTESTED: {
    bg: "rgba(16,185,129,0.15)",
    text: "#34d399",
    border: "rgba(16,185,129,0.3)",
    label: "Auto-Contested",
  },
  NEEDS_REVIEW: {
    bg: "rgba(245,158,11,0.15)",
    text: "#fbbf24",
    border: "rgba(245,158,11,0.3)",
    label: "Needs Review",
  },
  AUTO_ACCEPTED: {
    bg: "rgba(239,68,68,0.15)",
    text: "#f87171",
    border: "rgba(239,68,68,0.3)",
    label: "Auto-Accepted",
  },
  MANUALLY_CONTESTED: {
    bg: "rgba(124,58,237,0.15)",
    text: "#a78bfa",
    border: "rgba(124,58,237,0.3)",
    label: "Manual Contest",
  },
  WON: {
    bg: "rgba(16,185,129,0.2)",
    text: "#10b981",
    border: "rgba(16,185,129,0.4)",
    label: "Won",
  },
  LOST: {
    bg: "rgba(239,68,68,0.2)",
    text: "#ef4444",
    border: "rgba(239,68,68,0.4)",
    label: "Lost",
  },
};

function StatusBadge({ status }: { status: string }) {
  const style = STATUS_STYLES[status] || STATUS_STYLES.RECEIVED;
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        padding: "4px 12px",
        borderRadius: "20px",
        fontSize: "12px",
        fontWeight: 600,
        background: style.bg,
        color: style.text,
        border: `1px solid ${style.border}`,
        letterSpacing: "0.3px",
      }}
    >
      {style.label}
    </span>
  );
}

function ConfidenceBar({ score }: { score: number | null }) {
  if (score === null || score === undefined) {
    return (
      <span style={{ color: "var(--color-text-dim)", fontSize: "13px" }}>
        —
      </span>
    );
  }

  const color =
    score > 80 ? "#10b981" : score >= 40 ? "#f59e0b" : "#ef4444";

  return (
    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
      <div
        style={{
          width: "60px",
          height: "6px",
          borderRadius: "3px",
          background: "rgba(255,255,255,0.06)",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${score}%`,
            height: "100%",
            borderRadius: "3px",
            background: color,
            transition: "width 0.5s ease",
          }}
        />
      </div>
      <span
        style={{
          fontSize: "13px",
          fontWeight: 600,
          color,
          minWidth: "32px",
        }}
      >
        {score.toFixed(0)}
      </span>
    </div>
  );
}

export default function DisputeTable({ disputes, onRefresh }: Props) {
  const [overrideLoading, setOverrideLoading] = useState<string | null>(
    null
  );
  const [error, setError] = useState<string | null>(null);

  const handleOverride = async (disputeId: string) => {
    setOverrideLoading(disputeId);
    setError(null);
    try {
      await manualOverride(disputeId);
      onRefresh();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to override dispute"
      );
    } finally {
      setOverrideLoading(null);
    }
  };

  return (
    <div
      className="animate-fade-in"
      style={{
        background: "var(--color-surface-card)",
        borderRadius: "16px",
        border: "1px solid var(--color-border)",
        overflow: "hidden",
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "20px 24px",
          borderBottom: "1px solid var(--color-border)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div>
          <h2
            style={{
              fontSize: "16px",
              fontWeight: 700,
              color: "#fff",
              margin: 0,
            }}
          >
            Chargeback Disputes
          </h2>
          <p
            style={{
              fontSize: "13px",
              color: "var(--color-text-dim)",
              margin: "4px 0 0",
            }}
          >
            {disputes.length} disputes loaded
          </p>
        </div>
        <button
          onClick={onRefresh}
          style={{
            padding: "8px 16px",
            borderRadius: "8px",
            border: "1px solid var(--color-border)",
            background: "transparent",
            color: "var(--color-text-muted)",
            fontSize: "13px",
            fontWeight: 500,
            cursor: "pointer",
            transition: "all 0.2s",
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLElement).style.borderColor =
              "var(--color-accent)";
            (e.currentTarget as HTMLElement).style.color =
              "var(--color-accent)";
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLElement).style.borderColor =
              "var(--color-border)";
            (e.currentTarget as HTMLElement).style.color =
              "var(--color-text-muted)";
          }}
        >
          ↻ Refresh
        </button>
      </div>

      {error && (
        <div
          style={{
            padding: "12px 24px",
            background: "rgba(239,68,68,0.1)",
            borderBottom: "1px solid rgba(239,68,68,0.2)",
            color: "#f87171",
            fontSize: "13px",
          }}
        >
          ⚠️ {error}
        </div>
      )}

      {/* Table */}
      <div style={{ overflowX: "auto" }}>
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            fontSize: "14px",
          }}
        >
          <thead>
            <tr
              style={{
                borderBottom: "1px solid var(--color-border)",
              }}
            >
              {[
                "Dispute ID",
                "Payment ID",
                "Amount",
                "Confidence",
                "Status",
                "Reason",
                "Created",
                "Action",
              ].map((h) => (
                <th
                  key={h}
                  style={{
                    padding: "12px 16px",
                    textAlign: "left",
                    fontWeight: 600,
                    fontSize: "12px",
                    color: "var(--color-text-dim)",
                    textTransform: "uppercase",
                    letterSpacing: "0.5px",
                    whiteSpace: "nowrap",
                  }}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {disputes.map((d, idx) => (
              <tr
                key={d.dispute_id}
                style={{
                  borderBottom: "1px solid var(--color-border)",
                  transition: "background 0.15s",
                  background:
                    idx % 2 === 0
                      ? "transparent"
                      : "rgba(255,255,255,0.015)",
                }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLElement).style.background =
                    "rgba(82,143,240,0.04)";
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLElement).style.background =
                    idx % 2 === 0
                      ? "transparent"
                      : "rgba(255,255,255,0.015)";
                }}
              >
                <td
                  style={{
                    padding: "14px 16px",
                    fontFamily: "monospace",
                    fontSize: "13px",
                    color: "var(--color-accent-glow)",
                  }}
                >
                  {d.dispute_id}
                </td>
                <td
                  style={{
                    padding: "14px 16px",
                    fontFamily: "monospace",
                    fontSize: "13px",
                    color: "var(--color-text-muted)",
                  }}
                >
                  {d.payment_id || "—"}
                </td>
                <td
                  style={{
                    padding: "14px 16px",
                    fontWeight: 600,
                    color: "#fff",
                  }}
                >
                  ₹
                  {d.amount.toLocaleString("en-IN", {
                    maximumFractionDigits: 2,
                  })}
                </td>
                <td style={{ padding: "14px 16px" }}>
                  <ConfidenceBar score={d.confidence_score} />
                </td>
                <td style={{ padding: "14px 16px" }}>
                  <StatusBadge status={d.status} />
                </td>
                <td
                  style={{
                    padding: "14px 16px",
                    color: "var(--color-text-muted)",
                    fontSize: "13px",
                  }}
                >
                  {d.reason_code || "—"}
                </td>
                <td
                  style={{
                    padding: "14px 16px",
                    color: "var(--color-text-dim)",
                    fontSize: "13px",
                    whiteSpace: "nowrap",
                  }}
                >
                  {d.created_at
                    ? new Date(d.created_at).toLocaleDateString("en-IN", {
                        day: "2-digit",
                        month: "short",
                        year: "numeric",
                      })
                    : "—"}
                </td>
                <td style={{ padding: "14px 16px" }}>
                  {d.status === "NEEDS_REVIEW" ? (
                    <button
                      onClick={() => handleOverride(d.dispute_id)}
                      disabled={overrideLoading === d.dispute_id}
                      style={{
                        padding: "6px 14px",
                        borderRadius: "8px",
                        border: "none",
                        background:
                          overrideLoading === d.dispute_id
                            ? "rgba(82,143,240,0.3)"
                            : "linear-gradient(135deg, #528ff0 0%, #6ea8ff 100%)",
                        color: "#fff",
                        fontSize: "12px",
                        fontWeight: 600,
                        cursor:
                          overrideLoading === d.dispute_id
                            ? "not-allowed"
                            : "pointer",
                        transition: "all 0.2s",
                        boxShadow: "0 2px 8px rgba(82,143,240,0.25)",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {overrideLoading === d.dispute_id
                        ? "Contesting..."
                        : "⚡ Manual Override"}
                    </button>
                  ) : (
                    <span
                      style={{
                        fontSize: "12px",
                        color: "var(--color-text-dim)",
                      }}
                    >
                      —
                    </span>
                  )}
                </td>
              </tr>
            ))}
            {disputes.length === 0 && (
              <tr>
                <td
                  colSpan={8}
                  style={{
                    padding: "48px 16px",
                    textAlign: "center",
                    color: "var(--color-text-dim)",
                    fontSize: "14px",
                  }}
                >
                  No disputes found. Waiting for webhook events...
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
