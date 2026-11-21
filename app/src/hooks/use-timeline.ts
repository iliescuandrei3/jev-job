import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { apiGet } from "@/lib/api";
import type { DashboardFilters, TimelineOut } from "@/lib/types";

/** GET /dashboard/timeline: weekly chart and streak heatmap over the last `weeks` weeks (4–104). Filtered. */
export function useTimeline(filters: DashboardFilters, weeks: number) {
  return useQuery({
    queryKey: ["dashboard", "timeline", filters, weeks],
    queryFn: ({ signal }) => apiGet<TimelineOut>("/dashboard/timeline", { ...filters, weeks }, signal),
    // Keep the old charts on screen while a filter change loads
    placeholderData: keepPreviousData,
  });
}
