import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/lib/api";
import type { FilterOptions } from "@/lib/types";

/** GET /dashboard/filters: companies, roles and statuses for the search bar. Unfiltered. */
export function useFilterOptions() {
  return useQuery({
    queryKey: ["dashboard", "filters"],
    queryFn: ({ signal }) => apiGet<FilterOptions>("/dashboard/filters", {}, signal),
  });
}
