import { useCallback, useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ApiError, API_BASE_URL, apiPost } from "@/lib/api";
import { AUTH_QUERY_KEY } from "@/lib/query-client";
import type { JobState, JobStatus, RefreshResponse } from "@/lib/types";
import { useAuth } from "@/hooks/use-auth";

/** The running job's id survives a page reload, so the progress reattaches */
const ACTIVE_JOB_STORAGE_KEY = "email-refresh-job-id";
const TERMINAL_STATUSES: readonly JobStatus[] = ["completed", "failed"];
const JOB_STATUSES: readonly JobStatus[] = ["pending", "running", "completed", "failed"];
const MAX_RETRY_DELAY_MS = 10_000;

function isJobState(value: unknown): value is JobState {
  if (typeof value !== "object" || value === null) return false;
  const state = value as Record<string, unknown>;
  return (
    JOB_STATUSES.includes(state.status as JobStatus) &&
    typeof state.task_name === "string" &&
    typeof state.message === "string"
  );
}

/** The running job's id from a 409 (`detail: { message, job_id }`), if that's what the error is. */
function activeJobId(error: unknown): string | null {
  if (!(error instanceof ApiError) || error.status !== 409) return null;
  const { detail } = error;
  if (typeof detail !== "object" || detail === null || !("job_id" in detail)) return null;
  return typeof detail.job_id === "string" ? detail.job_id : null;
}

function webSocketUrl(jobId: string): string {
  const url = new URL(`/emails/ws/sync/${encodeURIComponent(jobId)}`, API_BASE_URL || window.location.origin);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  return url.toString();
}

/**
 * "Sync now": POST /emails/refresh, then follow /emails/ws/sync/{job_id} until the job ends.
 * A 409 (a sync is already running) attaches to that job. When a job completes, every dashboard
 * query refetches.
 */
export function useSyncJob() {
  const queryClient = useQueryClient();
  const { csrfToken } = useAuth();
  const [jobId, setJobId] = useState<string | null>(() => window.localStorage.getItem(ACTIVE_JOB_STORAGE_KEY));
  const [jobState, setJobState] = useState<JobState | null>(() =>
    jobId ? { status: "pending", task_name: "Sync emails", message: "Reconnecting to the running sync…" } : null,
  );
  const [connectionMessage, setConnectionMessage] = useState<string | null>(null);

  const attach = useCallback((id: string) => {
    window.localStorage.setItem(ACTIVE_JOB_STORAGE_KEY, id);
    setJobId(id);
    setJobState({ status: "pending", task_name: "Sync emails", message: "Sync queued. Waiting for progress…" });
  }, []);

  const start = useMutation({
    mutationFn: () => apiPost<RefreshResponse>("/emails/refresh", csrfToken),
    onSuccess: (body) => attach(body.job_id),
    onError: (error) => {
      const id = activeJobId(error);
      if (id) attach(id);
    },
  });

  useEffect(() => {
    if (!jobId) return;

    let isDisposed = false;
    let reconnectTimer: number | undefined;
    let retryDelay = 1000;
    let socket: WebSocket | null = null;

    const finish = (state: JobState) => {
      if (window.localStorage.getItem(ACTIVE_JOB_STORAGE_KEY) === jobId) {
        window.localStorage.removeItem(ACTIVE_JOB_STORAGE_KEY);
      }
      isDisposed = true;
      socket?.close();
      setJobId(null);
      if (state.status === "completed") {
        // Everything but the session: every widget refetches with the new emails
        void queryClient.invalidateQueries({ predicate: (query) => query.queryKey[0] !== AUTH_QUERY_KEY[0] });
      }
    };

    const connect = () => {
      if (isDisposed) return;
      setConnectionMessage("Connecting to sync updates…");
      socket = new WebSocket(webSocketUrl(jobId));

      socket.onopen = () => {
        retryDelay = 1000;
        setConnectionMessage(null);
      };

      socket.onmessage = (event: MessageEvent<string>) => {
        let parsed: unknown;
        try {
          parsed = JSON.parse(event.data);
        } catch {
          setConnectionMessage("Received an unreadable sync update.");
          return;
        }
        if (!isJobState(parsed)) {
          setConnectionMessage("Received an invalid sync update.");
          return;
        }
        setJobState(parsed);
        if (TERMINAL_STATUSES.includes(parsed.status)) finish(parsed);
      };

      socket.onerror = () => socket?.close();

      socket.onclose = () => {
        if (isDisposed) return;
        setConnectionMessage("Connection lost. Reconnecting…");
        reconnectTimer = window.setTimeout(connect, retryDelay);
        retryDelay = Math.min(retryDelay * 2, MAX_RETRY_DELAY_MS);
      };
    };

    connect();
    return () => {
      isDisposed = true;
      if (reconnectTimer !== undefined) window.clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, [jobId, queryClient]);

  // A 409 isn't an error for the user: the hook attached to the running job instead
  const error = start.error && !activeJobId(start.error) ? start.error : null;

  return {
    start: () => start.mutate(),
    isStarting: start.isPending,
    isRunning: jobId !== null,
    jobState,
    connectionMessage,
    error,
  };
}
