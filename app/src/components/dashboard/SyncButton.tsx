import { RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";
import type { JobState } from "@/lib/types";

/** "Sync now" plus the running job's latest progress message. */
export function SyncButton({
  onSync,
  isStarting,
  isRunning,
  jobState,
  connectionMessage,
  error,
}: {
  onSync: () => void;
  isStarting: boolean;
  isRunning: boolean;
  jobState: JobState | null;
  connectionMessage: string | null;
  error: Error | null;
}) {
  const isBusy = isStarting || isRunning;

  return (
    <div className="flex flex-col items-end gap-1 text-sm">
      <button
        type="button"
        onClick={onSync}
        disabled={isBusy}
        className="inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-xs transition-colors hover:border-primary disabled:opacity-50"
      >
        <RefreshCw className={cn("h-3.5 w-3.5", isBusy && "animate-spin")} />
        {isStarting ? "Starting sync…" : isRunning ? "Syncing…" : "Sync now"}
      </button>
      <p aria-live="polite" className="max-w-xs text-right text-xs">
        {error ? (
          <span className="text-destructive">Sync could not start. {error.message}</span>
        ) : (
          jobState && (
            <span className={jobState.status === "failed" ? "text-destructive" : "text-muted-foreground"}>
              {jobState.message}
            </span>
          )
        )}
        {connectionMessage && <span className="block text-muted-foreground">{connectionMessage}</span>}
      </p>
    </div>
  );
}
