import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { apiGet } from "@/lib/api";
import type { DashboardFilters, OverviewOut } from "@/lib/types";

/** GET /dashboard/overview: KPI tiles, funnel, status donut and insights. Filtered. */
export function useOverview(filters: DashboardFilters) {
  return useQuery({
    queryKey: ["dashboard", "overview", filters],
    queryFn: ({ signal }) => apiGet<OverviewOut>("/dashboard/overview", { ...filters }, signal),
    // Keep the old numbers on screen while a filter change loads
    placeholderData: keepPreviousData,
  });
}
