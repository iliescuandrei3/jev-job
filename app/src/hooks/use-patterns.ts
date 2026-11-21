import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { apiGet } from "@/lib/api";
import type { DashboardFilters, PatternsOut } from "@/lib/types";

/** GET /dashboard/patterns: roles, weekday and hour-of-day charts. Filtered. */
export function usePatterns(filters: DashboardFilters) {
  return useQuery({
    queryKey: ["dashboard", "patterns", filters],
    queryFn: ({ signal }) => apiGet<PatternsOut>("/dashboard/patterns", { ...filters }, signal),
    // Keep the old charts on screen while a filter change loads
    placeholderData: keepPreviousData,
  });
}
