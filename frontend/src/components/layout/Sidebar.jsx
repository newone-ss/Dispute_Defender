import React from "react";
import { NavLink } from "react-router-dom";
import { 
  ShieldCheck, 
  LayoutDashboard, 
  FileText, 
  Cpu
} from "lucide-react";

export function Sidebar() {
  const navItems = [
    { to: "/", label: "Overview", icon: LayoutDashboard, badge: null },
    { to: "/disputes", label: "Disputes Ledger", icon: FileText, badge: "14" },
    { to: "/simulator", label: "Scenario Simulator", icon: Cpu, badge: "Live" },
  ];

  return (
    <aside className="w-64 shrink-0 bg-white border-r border-slate-200 flex flex-col h-screen sticky top-0 select-none z-30">
      {/* Brand Header */}
      <div className="p-4 border-b border-slate-200 flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-emerald-50 border border-emerald-200/80 flex items-center justify-center text-emerald-600 shrink-0">
          <ShieldCheck className="w-5 h-5" />
        </div>
        <div>
          <div className="flex items-center gap-1.5">
            <h1 className="text-sm font-bold text-[#172033] tracking-tight">Dispute Defender</h1>
            <span className="px-1.5 py-0.2 rounded text-[10px] font-mono bg-slate-100 text-slate-600 border border-slate-200 font-semibold">
              v2.4
            </span>
          </div>
          <p className="text-[11px] text-slate-500">Razorpay Risk Ops & UDIR</p>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        <div className="px-3 pb-2 text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
          Operations
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center justify-between px-3 py-2 text-xs font-medium rounded-lg transition-all ${
                  isActive
                    ? "bg-emerald-50/80 text-emerald-800 border border-emerald-200/80 font-semibold shadow-xs"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <div className="flex items-center gap-2.5">
                    <Icon className={`w-4 h-4 ${isActive ? "text-emerald-700" : "text-slate-500"}`} />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span
                      className={`text-[10px] font-mono px-1.5 py-0.5 rounded-full ${
                        isActive
                          ? "bg-emerald-100 text-emerald-800"
                          : "bg-slate-100 text-slate-500"
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Footer Profile & Live Status */}
      <div className="p-3 border-t border-slate-200 bg-slate-50/50 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-emerald-100 border border-emerald-200 flex items-center justify-center text-emerald-700 font-semibold text-xs">
            RO
          </div>
          <div>
            <div className="text-xs font-semibold text-[#172033]">Risk Officer</div>
            <div className="text-[11px] text-slate-500">Risk Operations</div>
          </div>
        </div>
      </div>
    </aside>
  );
}
