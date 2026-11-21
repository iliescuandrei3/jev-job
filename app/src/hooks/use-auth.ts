import { createContext, useContext } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { UnauthorizedError, apiGet, apiPost } from "@/lib/api";
import { AUTH_QUERY_KEY } from "@/lib/query-client";
import type { AuthUser, MeResponse } from "@/lib/types";

export interface AuthState {
  user: AuthUser;
  /** Sent as `X-CSRF-Token` on every mutation (logout, sync). */
  csrfToken: string;
}

/** Provided by `AuthGate` once `/auth/me` succeeds. */
export const AuthContext = createContext<AuthState | null>(null);

/** The signed-in user. Only usable below `AuthGate`. */
export function useAuth(): AuthState {
  const auth = useContext(AuthContext);
  if (!auth) throw new Error("useAuth must be used inside <AuthGate>");
  return auth;
}

/** GET /auth/me. Resolves to `null` when signed out (401) instead of failing. */
export function useMe() {
  return useQuery({
    queryKey: AUTH_QUERY_KEY,
    queryFn: async ({ signal }) => {
      try {
        return await apiGet<MeResponse>("/auth/me", {}, signal);
      } catch (error) {
        if (error instanceof UnauthorizedError) return null;
        throw error;
      }
    },
    staleTime: Infinity,
  });
}

/** POST /auth/logout, then drop every cached dashboard query and show the sign-in screen. */
export function useLogout() {
  const queryClient = useQueryClient();
  const { csrfToken } = useAuth();
  return useMutation({
    mutationFn: () => apiPost<{ message: string }>("/auth/logout", csrfToken),
    onSettled: (_data, error) => {
      // A 401 means the session was already gone, which is the same outcome
      if (error && !(error instanceof UnauthorizedError)) return;
      // Keep the auth query itself: AuthGate observes it, so setting it to null shows the sign-in screen
      queryClient.removeQueries({ predicate: (query) => query.queryKey[0] !== AUTH_QUERY_KEY[0] });
      queryClient.setQueryData(AUTH_QUERY_KEY, null);
    },
  });
}
