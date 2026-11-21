import { QueryCache, QueryClient } from "@tanstack/react-query";
import { UnauthorizedError } from "./api";

/** Query key of GET /auth/me. Its data is `null` while signed out. */
export const AUTH_QUERY_KEY = ["auth", "me"] as const;

export const queryClient: QueryClient = new QueryClient({
  queryCache: new QueryCache({
    // A query that gets a 401 later (session expired) sends the app back to the sign-in screen
    onError: (error) => {
      if (error instanceof UnauthorizedError) queryClient.setQueryData(AUTH_QUERY_KEY, null);
    },
  }),
  defaultOptions: {
    queries: {
      retry: (failureCount, error) => !(error instanceof UnauthorizedError) && failureCount < 2,
      refetchOnWindowFocus: false,
      staleTime: 60_000,
    },
  },
});
