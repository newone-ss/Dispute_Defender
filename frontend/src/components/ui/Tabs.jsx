import React from "react";

export function Tabs({ tabs, activeTab, onChange, className = "" }) {
  return (
    <div className={`flex items-center gap-1 border-b border-slate-200 bg-slate-100/70 p-1 rounded-xl ${className}`}>
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        const Icon = tab.icon;

        return (
          <button
            key={tab.id}
            type="button"
            onClick={() => onChange(tab.id)}
            className={`flex items-center gap-2 px-3.5 py-2 text-xs font-medium rounded-lg transition-all ${
              isActive
                ? "bg-white text-slate-900 shadow-xs border border-slate-200/90 font-semibold"
                : "text-slate-600 hover:text-slate-900 hover:bg-white/50"
            }`}
          >
            {Icon && <Icon className={`w-3.5 h-3.5 ${isActive ? "text-emerald-600" : "text-slate-500"}`} />}
            <span>{tab.label}</span>
            {tab.badge !== undefined && tab.badge !== null && (
              <span className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
                isActive ? "bg-slate-100 text-slate-700 font-medium" : "bg-slate-200/70 text-slate-600"
              }`}>
                {tab.badge}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
