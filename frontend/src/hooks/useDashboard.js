import { useQuery } from "@tanstack/react-query";
import { getDashboard } from "../api/dashboard";

export function useDashboard() {
  return useQuery({
    queryKey: ["dashboard-metrics"],
    queryFn: getDashboard,
    staleTime: 1000 * 3, // 3 seconds
    refetchInterval: 5000, // Poll every 5s for live ROI/dispute metrics
    refetchOnWindowFocus: true, // Instantly refresh when returning from Postman
  });
}
