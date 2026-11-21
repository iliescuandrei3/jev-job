// Fetch wrapper for the FastAPI backend. Only hooks/ call these functions.

export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/+$/, "");

export const apiUrl = (path: string) => `${API_BASE_URL}${path}`;

/** Where the sign-in button sends the browser (Google OAuth, then back to the app). */
export const loginUrl = () => apiUrl("/auth/login");

/** The session is missing or expired (HTTP 401). */
export class UnauthorizedError extends Error {
  constructor() {
    super("Not authenticated");
    this.name = "UnauthorizedError";
  }
}

/** Any other non-2xx response. */
export class ApiError extends Error {
  readonly status: number;
  /** The response's `detail` field when the body was JSON, e.g. `{ message, job_id }` on a 409 from /emails/refresh. */
  readonly detail: unknown;

  constructor(status: number, message: string, detail?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

type ParamValue = string | number | boolean | null | undefined | readonly (string | number)[];
export type QueryParams = Record<string, ParamValue>;

/** Lists become repeated keys (`?companies=a&companies=b`); empty values are left out. */
export function toSearchParams(params: QueryParams): URLSearchParams {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === null || value === undefined || value === "") continue;
    if (Array.isArray(value)) {
      for (const item of value) search.append(key, String(item));
    } else {
      search.append(key, String(value));
    }
  }
  return search;
}

async function request<T>(path: string, init: RequestInit): Promise<T> {
  const res = await fetch(apiUrl(path), { ...init, credentials: "include" });
  if (res.status === 401) throw new UnauthorizedError();
  if (!res.ok) {
    let text = res.statusText;
    let detail: unknown;
    try {
      const body: unknown = await res.json();
      if (typeof body === "object" && body !== null && "detail" in body) {
        detail = body.detail;
        if (typeof body.detail === "string") text = body.detail;
      }
    } catch {
      // not JSON: keep statusText
    }
    throw new ApiError(res.status, `Request failed (${res.status}): ${text}`, detail);
  }
  return (await res.json()) as T;
}

export function apiGet<T>(path: string, params: QueryParams = {}, signal?: AbortSignal): Promise<T> {
  const query = toSearchParams(params).toString();
  return request<T>(query ? `${path}?${query}` : path, { signal });
}

/** Mutations need the CSRF token from /auth/me (checked by `verify_csrf_and_origin`). */
export function apiPost<T>(path: string, csrfToken: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: "POST",
    headers: {
      "X-CSRF-Token": csrfToken,
      ...(body === undefined ? {} : { "Content-Type": "application/json" }),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}
