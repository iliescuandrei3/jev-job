import { STATUS_META } from "@/lib/status";
import type { Status } from "@/lib/types";

export function StatusDot({ status, className = "" }: { status: Status; className?: string }) {
  return <span className={`inline-block h-2 w-2 shrink-0 rounded-full ${STATUS_META[status].bg} ${className}`} />;
}

export function StatusPill({ status }: { status: Status }) {
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 font-mono text-[11px] ${STATUS_META[status].text}`}>
      <StatusDot status={status} />
      {STATUS_META[status].label}
    </span>
  );
}
