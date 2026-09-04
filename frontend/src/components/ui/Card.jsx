import React from "react";

export function Card({
  children,
  className = "",
  variant = "default", // default, subtle, elevated, glass
  header,
  footer,
  ...props
}) {
  const variantStyles = {
    default: "bg-white border border-slate-200/90 shadow-[0_4px_16px_rgba(15,23,42,0.05)]",
    subtle: "bg-white border border-slate-200/70 shadow-[0_2px_8px_rgba(15,23,42,0.03)]",
    elevated: "bg-white border border-slate-200 shadow-[0_8px_24px_rgba(15,23,42,0.07)]",
    glass: "bg-white/95 backdrop-blur-md border border-slate-200/90 shadow-[0_4px_16px_rgba(15,23,42,0.06)]",
  }[variant] || "bg-white border border-slate-200/90 shadow-[0_4px_16px_rgba(15,23,42,0.05)]";

  return (
    <div className={`rounded-xl overflow-hidden transition-all duration-200 ${variantStyles} ${className}`} {...props}>
      {header && (
        <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/40">
          {header}
        </div>
      )}
      <div className="p-5">{children}</div>
      {footer && (
        <div className="px-5 py-3.5 bg-slate-50/70 border-t border-slate-100 text-xs text-slate-500">
          {footer}
        </div>
      )}
    </div>
  );
}
