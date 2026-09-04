import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getDisputes } from "../api/disputes";

export function useDisputes() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("ALL");
  const [sortBy, setSortBy] = useState("timestamp"); // timestamp, amount, riskScore
  const [sortOrder, setSortOrder] = useState("desc");

  const query = useQuery({
    queryKey: ["disputes", { search, status, sortBy, sortOrder }],
    queryFn: () => getDisputes({ search, status }),
    staleTime: 1000 * 20,
    refetchOnWindowFocus: false,
  });

  const rawData = query.data;
  const rawList = Array.isArray(rawData)
    ? rawData
    : Array.isArray(rawData?.disputes)
    ? rawData.disputes
    : [];

  const disputes = rawList.map((d) => ({
    ...d,
    id: d.razorpay_dispute_id || d.id || d.dispute_id,
    amount: d.amount ?? d.amount_inr ?? (d.amount_paise ? d.amount_paise / 100 : 0),
    riskScore: d.riskScore ?? d.score ?? 50,
    timestamp: d.timestamp || d.created_at || new Date().toISOString(),
    customerName: d.customerName || (d.payment_id ? `Order #${d.payment_id.slice(-6)}` : 'Customer'),
    orderId: d.orderId || d.payment_id || 'N/A',
    status: (typeof d.status === 'string' ? d.status.toUpperCase() : 'NEEDS_REVIEW'),
    evidenceSignals: d.evidenceSignals || {
      doorstepOtp: { verified: d.telemetry?.otp?.verified ?? d.telemetry?.otp_verified ?? false },
      gpsGeofence: { distanceMeters: d.telemetry?.geofence?.distance_m ?? d.telemetry?.gps_distance_meters ?? 25 },
      weightDelta: {
        originGrams: d.telemetry?.weight?.shipped_g || 500,
        doorstepGrams: d.telemetry?.weight?.delivered_g || 500,
        deltaPct: 0,
      },
      proofOfDelivery: { verified: d.telemetry?.delivery_signature ?? true },
    },
  }));

  // Sort client-side for immediate responsive feel
  const sortedDisputes = [...disputes].sort((a, b) => {
    let aVal = a[sortBy];
    let bVal = b[sortBy];

    if (sortBy === "timestamp") {
      aVal = new Date(aVal).getTime();
      bVal = new Date(bVal).getTime();
    }

    if (aVal < bVal) return sortOrder === "asc" ? -1 : 1;
    if (aVal > bVal) return sortOrder === "asc" ? 1 : -1;
    return 0;
  });

  return {
    ...query,
    disputes: sortedDisputes,
    search,
    setSearch,
    status,
    setStatus,
    sortBy,
    setSortBy,
    sortOrder,
    setSortOrder,
    totalCount: sortedDisputes.length,
  };
}
