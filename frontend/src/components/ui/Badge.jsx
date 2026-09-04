import React from "react";
import { DECISION_TYPES } from "../../utils/constants";

export function Badge({ 
  status, 
  variant, 
  children, 
  className = "", 
  showDot = true,
  size = "md" 
}) {
  const decisionConfig = status ? DECISION_TYPES[status] : null;

  let baseClass = "inline-flex items-center font-medium rounded-full transition-colors";
  let colorClass = "";
  let dotColor = "";

  const sizeClass = size === "sm" 
    ? "px-2 py-0.5 text-xs gap-1.5" 
    : "px-2.5 py-1 text-xs gap-1.5";

  if (decisionConfig) {
    colorClass = decisionConfig.badgeClass;
    dotColor = decisionConfig.dotClass;
  } else {
    switch (variant) {
      case "emerald":
      case "success":
        colorClass = "bg-emerald-50 text-emerald-700 border border-emerald-200/90";
        dotColor = "bg-emerald-600";
        break;
      case "amber":
      case "warning":
        colorClass = "bg-amber-50 text-amber-700 border border-amber-200/90";
        dotColor = "bg-amber-500";
        break;
      case "rose":
      case "danger":
        colorClass = "bg-rose-50 text-rose-700 border border-rose-200/90";
        dotColor = "bg-rose-600";
        break;
      case "sky":
      case "info":
        colorClass = "bg-sky-50 text-sky-700 border border-sky-200/90";
        dotColor = "bg-sky-600";
        break;
      case "purple":
      case "violet":
        colorClass = "bg-purple-50 text-purple-700 border border-purple-200/90";
        dotColor = "bg-purple-600";
        break;
      case "slate":
      default:
        colorClass = "bg-slate-100 text-slate-700 border border-slate-200";
        dotColor = "bg-slate-500";
        break;
    }
  }

  return (
    <span className={`${baseClass} ${sizeClass} ${colorClass} ${className}`}>
      {showDot && <span className={`w-1.5 h-1.5 rounded-full ${dotColor}`} />}
      <span>{children || (decisionConfig ? decisionConfig.label : status)}</span>
    </span>
  );
}
