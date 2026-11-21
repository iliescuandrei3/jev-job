import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { apiGet } from "@/lib/api";
import type { CompanyDetailOut, CompanyOut, DashboardFilters } from "@/lib/types";

/** GET /companies: filtered companies for the grid, most applications first. */
export function useCompanies(filters: DashboardFilters) {
  return useQuery({
    queryKey: ["companies", "list", filters],
    queryFn: ({ signal }) => apiGet<CompanyOut[]>("/companies", { ...filters }, signal),
    // Keep the old tiles on screen while a filter change loads
    placeholderData: keepPreviousData,
  });
}

/** GET /companies/{key}: one company's whole history (unfiltered). Idle while `key` is empty. */
export function useCompany(key: string | null | undefined) {
  return useQuery({
    queryKey: ["companies", "detail", key],
    queryFn: ({ signal }) => apiGet<CompanyDetailOut>(`/companies/${encodeURIComponent(key ?? "")}`, {}, signal),
    enabled: Boolean(key),
  });
}
