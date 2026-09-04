import React from "react";
import { Search, ArrowUpDown } from "lucide-react";

export function DisputeFilters({
  search,
  onSearchChange,
  status,
  onStatusChange,
  sortBy,
  onSortByChange,
  sortOrder,
  onToggleSortOrder,
  totalCount,
}) {
  const statusOptions = [
    { key: "ALL", label: "All Disputes" },
    { key: "AUTO_CONTESTED", label: "Auto Contested" },
    { key: "NEEDS_REVIEW", label: "Needs Review" },
    { key: "AUTO_ACCEPTED", label: "Liability Released" },
  ];

  return (
    <div className="bg-white border border-slate-200/90 rounded-xl p-4 shadow-[0_2px_8px_rgba(15,23,42,0.04)] space-y-3">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        {/* Search Bar */}
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            placeholder="Search dispute ID, customer, AWB, or order..."
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-xs bg-slate-50/70 border border-slate-200 rounded-lg text-[#172033] placeholder-slate-400 focus:outline-none focus:border-slate-300 focus:bg-white transition-colors"
          />
        </div>

        {/* Right Sort Controls & Count */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <span>Sort by:</span>
            <select
              value={sortBy}
              onChange={(e) => onSortByChange(e.target.value)}
              className="bg-slate-50/70 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs text-slate-700 focus:outline-none focus:border-slate-300 focus:bg-white"
            >
              <option value="timestamp">Timestamp</option>
              <option value="amount">Disputed Amount</option>
              <option value="riskScore">Risk Score</option>
            </select>
            <button
              type="button"
              onClick={onToggleSortOrder}
              className="p-1.5 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg text-slate-600 transition-colors"
              title={sortOrder === "desc" ? "Descending" : "Ascending"}
            >
              <ArrowUpDown className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="text-xs font-mono text-slate-500 pl-3 border-l border-slate-200 hidden sm:block">
            <strong className="text-[#172033]">{totalCount}</strong> disputes
          </div>
        </div>
      </div>

      {/* Filter Tabs / Pills */}
      <div className="flex items-center gap-1.5 pt-1 overflow-x-auto">
        <span className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold mr-1 shrink-0">
          Status:
        </span>
        {statusOptions.map((opt) => {
          const isActive = status === opt.key;
          return (
            <button
              key={opt.key}
              type="button"
              onClick={() => onStatusChange(opt.key)}
              className={`px-3 py-1 text-xs font-medium rounded-lg transition-all shrink-0 ${
                isActive
                  ? "bg-slate-100 text-[#172033] border border-slate-200 font-semibold shadow-xs"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-50 border border-transparent"
              }`}
            >
              {opt.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
