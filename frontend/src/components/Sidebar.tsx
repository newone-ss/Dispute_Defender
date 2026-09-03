import React from "react";
import { NavLink } from "react-router-dom";

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 min-h-screen bg-gradient-to-b from-[#07162c] via-[#0a0e1a] to-[#070b14] border-r border-slate-800/80 flex flex-col fixed top-0 left-0 z-40">
      {/* Brand Header */}
      <div className="p-6 border-b border-slate-800/70">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-xl shadow-lg shadow-blue-500/25">
            🛡️
          </div>
          <div>
            <div className="font-bold text-base text-white tracking-tight leading-tight">
              Dispute Defender
            </div>
            <div className="text-[11px] font-medium text-blue-400 mt-0.5 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Razorpay Risk Shield
            </div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="p-4 flex-1 space-y-1.5">
        <NavLink
          to="/"
          end
          className={({ isActive }) =>
            `flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
              isActive
                ? "bg-blue-600/15 text-blue-300 border border-blue-500/30 shadow-sm"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
            }`
          }
        >
          <span className="text-lg">📊</span>
          <span>Financial Dashboard</span>
        </NavLink>

        <NavLink
          to="/disputes"
          className={({ isActive }) =>
            `flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
              isActive
                ? "bg-blue-600/15 text-blue-300 border border-blue-500/30 shadow-sm"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
            }`
          }
        >
          <span className="text-lg">⚔️</span>
          <span>Disputes Queue</span>
        </NavLink>
      </nav>

      {/* System Status & Hackathon Card */}
      <div className="p-4 m-4 rounded-xl bg-slate-900/90 border border-slate-800 text-xs text-slate-400 space-y-2">
        <div className="flex items-center justify-between text-[11px] font-semibold text-slate-300">
          <span>AI RISK MANAGER</span>
          <span className="px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300 text-[10px]">TRACK 2</span>
        </div>
        <p className="text-[11px] leading-relaxed text-slate-400">
          Deterministic telemetry audits, Jinja2 NPCI UDIR evidence drafting & consumer fairness gates.
        </p>
        <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-[10px] text-slate-400 font-mono">
          <span>MODE: MOCK / TEST</span>
          <span className="text-emerald-400">● LIVE</span>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
