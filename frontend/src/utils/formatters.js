// Currency formatter for Indian Rupees
export function formatINR(amount, includeDecimals = true) {
  if (amount === undefined || amount === null || isNaN(amount)) return "₹0";
  const num = Number(amount);
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: includeDecimals ? (num % 1 !== 0 ? 2 : 0) : 0,
    maximumFractionDigits: 2,
  }).format(num);
}

// Format relative time or timestamps
export function formatTimeAgo(dateString) {
  if (!dateString) return "—";
  const date = new Date(dateString);
  const now = new Date();
  const diffSec = Math.floor((now - date) / 1000);

  if (diffSec < 60) return `${Math.max(1, diffSec)}s ago`;
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHours = Math.floor(diffMin / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}

export function formatDateTime(dateString) {
  if (!dateString) return "—";
  const date = new Date(dateString);
  return date.toLocaleString("en-IN", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
}

// Truncate hash with ellipsis
export function truncateHash(hash, lead = 8, trail = 8) {
  if (!hash) return "—";
  if (hash.length <= lead + trail) return hash;
  return `${hash.slice(0, lead)}...${hash.slice(-trail)}`;
}

// Distance formatter
export function formatDistance(meters) {
  if (meters === undefined || meters === null) return "—";
  if (meters < 1000) return `${Math.round(meters)}m`;
  return `${(meters / 1000).toFixed(1)}km`;
}

// Weight delta formatter
export function formatWeightDelta(originGrams, doorstepGrams) {
  if (!originGrams || !doorstepGrams) return "—";
  const deltaGrams = originGrams - doorstepGrams;
  const pct = Math.abs((deltaGrams / originGrams) * 100).toFixed(1);
  const sign = deltaGrams > 0 ? "-" : "+";
  return `${sign}${Math.abs(deltaGrams)}g (${pct}%)`;
}
