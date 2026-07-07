import { useQuery } from "@tanstack/react-query";
import { getReports } from "../lib/butterbase";

export function useChildReports(childId: string) {
  return useQuery({
    queryKey: ["reports", childId],
    queryFn: () => getReports(childId),
    enabled: !!childId,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}
