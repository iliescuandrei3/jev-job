import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/lib/api";
import type { SyncOut } from "@/lib/types";

/** GET /dashboard/sync: email counts and the last sync time for the header. Unfiltered. */
export function useSyncStats() {
  return useQuery({
    queryKey: ["dashboard", "sync"],
    queryFn: ({ signal }) => apiGet<SyncOut>("/dashboard/sync", {}, signal),
  });
}
