import type { ReactNode } from "react";
import { AlertTriangle, RotateCw } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

/**
 * Shared loading / error / empty states for a widget. Renders `children` only once the data is there.
 * `skeleton` overrides the default placeholder so it can match the widget's shape.
 */
export function PanelState({
  isLoading,
  error,
  isEmpty = false,
  emptyText = "Nothing matches these filters.",
  onRetry,
  skeleton,
  children,
}: {
  isLoading: boolean;
  error?: Error | null;
  isEmpty?: boolean;
  emptyText?: string;
  onRetry?: () => void;
  skeleton?: ReactNode;
  children?: ReactNode;
}) {
  if (isLoading) {
    return (
      <div aria-busy="true" aria-label="Loading">
        {skeleton ?? (
          <div className="space-y-2">
            <Skeleton className="h-4 w-2/3" />
            <Skeleton className="h-4 w-1/2" />
            <Skeleton className="h-24 w-full" />
          </div>
        )}
      </div>
    );
  }

  if (error) {
    return (
      <div role="alert" className="flex flex-col items-start gap-2 text-sm">
        <span className="flex items-center gap-2 text-destructive">
          <AlertTriangle className="h-4 w-4" />
          Couldn&apos;t load this data.
        </span>
        <span className="font-mono text-xs text-muted-foreground">{error.message}</span>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-xs transition-colors hover:border-primary"
          >
            <RotateCw className="h-3 w-3" />
            Try again
          </button>
        )}
      </div>
    );
  }

  if (isEmpty) return <p className="text-sm text-muted-foreground">{emptyText}</p>;

  return <>{children}</>;
}
