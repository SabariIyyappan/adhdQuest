import { useQuery } from "@tanstack/react-query";
import { getChildren } from "../lib/butterbase";

export function useChildren() {
  return useQuery({
    queryKey: ["children"],
    queryFn: getChildren,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
