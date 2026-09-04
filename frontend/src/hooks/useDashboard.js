import { useQuery } from "@tanstack/react-query";
import { getDashboard } from "../api/dashboard";

export function useDashboard() {
  return useQuery({
    queryKey: ["dashboard-metrics"],
    queryFn: getDashboard,
    staleTime: 1000 * 30, // 30 seconds
    refetchOnWindowFocus: false,
  });
}
