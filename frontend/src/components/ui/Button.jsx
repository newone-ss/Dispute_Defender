import React from "react";
import { Loader2 } from "lucide-react";

export function Button({
  children,
  variant = "primary",
  size = "md",
  loading = false,
  disabled = false,
  icon: Icon,
  className = "",
  type = "button",
  onClick,
  ...props
}) {
  const baseClasses = "inline-flex items-center justify-center font-medium rounded-lg transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#F6F7F9] disabled:opacity-50 disabled:cursor-not-allowed select-none";

  const sizeClasses = {
    xs: "px-2 py-1 text-xs gap-1.5",
    sm: "px-3 py-1.5 text-xs gap-1.5",
    md: "px-4 py-2 text-sm gap-2",
    lg: "px-5 py-2.5 text-base gap-2.5",
  }[size] || "px-4 py-2 text-sm gap-2";

  const variantClasses = {
    primary: "bg-emerald-600 hover:bg-emerald-500 text-white font-semibold shadow-xs focus:ring-emerald-500",
    secondary: "bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 shadow-xs focus:ring-slate-400",
    outline: "bg-transparent hover:bg-slate-100 text-slate-700 border border-slate-300 focus:ring-slate-400",
    ghost: "bg-transparent hover:bg-slate-100 text-slate-600 hover:text-slate-900 focus:ring-slate-400",
    danger: "bg-rose-600 hover:bg-rose-500 text-white font-medium focus:ring-rose-500 shadow-xs",
    subtle: "bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200/80 focus:ring-slate-400",
  }[variant] || "";

  return (
    <button
      type="button"
      disabled={disabled || loading}
      onClick={onClick}
      className={`${baseClasses} ${sizeClasses} ${variantClasses} ${className}`}
      {...props}
    >
      {loading ? (
        <Loader2 className="w-4 h-4 animate-spin text-current" />
      ) : Icon ? (
        <Icon className="w-4 h-4 shrink-0" />
      ) : null}
      <span>{children}</span>
    </button>
  );
}
