import { useQuery } from "@tanstack/react-query";
import { getHealth } from "../api/health";

export function useHealth() {
  return useQuery({
    queryKey: ["backend-health"],
    queryFn: getHealth,
    refetchInterval: 15000, // poll every 15s
    staleTime: 10000,
    retry: 1,
  });
}
