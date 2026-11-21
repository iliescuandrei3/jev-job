import { useEffect, useMemo, useState } from "react";
import type { DashboardFilters } from "@/lib/types";

export const EMPTY_FILTERS: DashboardFilters = { q: "", companies: [], roles: [], statuses: [], rangeDays: null };

const SEARCH_DEBOUNCE_MS = 300;

/**
 * Filter state of the search bar. `filters` follows every keystroke (bind it to the inputs);
 * `queryFilters` has `q` debounced, so use it in query keys and API params.
 */
export function useDashboardFilters() {
  const [filters, setFilters] = useState<DashboardFilters>(EMPTY_FILTERS);
  const q = useDebouncedValue(filters.q.trim(), SEARCH_DEBOUNCE_MS);

  // Query keys are compared by value, so a new object per keystroke with the same `q` doesn't refetch
  const queryFilters = useMemo<DashboardFilters>(() => ({ ...filters, q }), [filters, q]);

  return { filters, setFilters, queryFilters };
}

function useDebouncedValue<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(value), delayMs);
    return () => window.clearTimeout(timer);
  }, [value, delayMs]);
  return debounced;
}
