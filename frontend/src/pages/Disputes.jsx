import React, { useState } from "react";
import { useDisputes } from "../hooks/useDisputes";
import { DisputeFilters } from "../components/disputes/DisputeFilters";
import { DisputesTable } from "../components/disputes/DisputesTable";
import { DeepAuditModal } from "../components/audit/DeepAuditModal";
import { RefreshCw } from "lucide-react";

export function Disputes() {
  const {
    disputes,
    isLoading,
    search,
    setSearch,
    status,
    setStatus,
    sortBy,
    setSortBy,
    sortOrder,
    setSortOrder,
    totalCount,
    refetch,
  } = useDisputes();

  const [selectedDisputeId, setSelectedDisputeId] = useState(null);

  const handleToggleSortOrder = () => {
    setSortOrder(sortOrder === "asc" ? "desc" : "asc");
  };

  return (
    <div className="space-y-5">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-slate-200/80">
        <div>
          <h2 className="text-base font-bold text-[#172033]">
            Disputes Operations Ledger
          </h2>
          <p className="text-xs text-slate-500">
            Multi-signal physical courier telemetry and deterministic NPCI arbitration routing
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => refetch()}
            className="px-3 py-1.5 rounded-lg bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 text-xs font-medium flex items-center gap-1.5 transition-colors shadow-xs"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <DisputeFilters
        search={search}
        onSearchChange={setSearch}
        status={status}
        onStatusChange={setStatus}
        sortBy={sortBy}
        onSortByChange={setSortBy}
        sortOrder={sortOrder}
        onToggleSortOrder={handleToggleSortOrder}
        totalCount={totalCount}
      />

      {/* Disputes Data Table */}
      <DisputesTable
        disputes={disputes}
        onSelectDispute={(id) => setSelectedDisputeId(id)}
        loading={isLoading}
      />

      {/* Deep Audit Modal */}
      <DeepAuditModal
        disputeId={selectedDisputeId}
        isOpen={Boolean(selectedDisputeId)}
        onClose={() => setSelectedDisputeId(null)}
      />
    </div>
  );
}
