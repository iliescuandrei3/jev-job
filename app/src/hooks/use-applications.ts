import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { apiGet } from "@/lib/api";
import type { ApplicationList, ApplicationOut, ApplicationSort, DashboardFilters } from "@/lib/types";

interface ApplicationsOptions {
  sort: ApplicationSort;
  /** Leave out for every matching application */
  limit?: number;
  offset?: number;
}

/** GET /applications: filtered, sorted and paged summaries (table rows, process lanes). */
export function useApplications(filters: DashboardFilters, { sort, limit, offset }: ApplicationsOptions) {
  return useQuery({
    queryKey: ["applications", "list", filters, { sort, limit, offset }],
    queryFn: ({ signal }) => apiGet<ApplicationList>("/applications", { ...filters, sort, limit, offset }, signal),
    // Keep the old rows on screen while a filter change loads
    placeholderData: keepPreviousData,
  });
}

/** GET /applications/{id}: one application with its templated emails. Idle while `id` is empty. */
export function useApplication(id: string | null | undefined) {
  return useQuery({
    queryKey: ["applications", "detail", id],
    queryFn: ({ signal }) => apiGet<ApplicationOut>(`/applications/${encodeURIComponent(id ?? "")}`, {}, signal),
    enabled: Boolean(id),
  });
}
