import type { DerivedStatus } from "@/lib/analytics";

export const STATUS_VAR: Record<DerivedStatus, string> = {
  Applied: "var(--status-applied)",
  Interview: "var(--status-interview)",
  Offer: "var(--status-offer)",
  Rejected: "var(--status-rejected)",
  Ghosted: "var(--status-ghosted)",
  Undefined: "var(--status-undefined)",
};

const BG: Record<DerivedStatus, string> = {
  Applied: "bg-applied",
  Interview: "bg-interview",
  Offer: "bg-offer",
  Rejected: "bg-rejected",
  Ghosted: "bg-ghosted",
  Undefined: "bg-undefined",
};
const TEXT: Record<DerivedStatus, string> = {
  Applied: "text-applied",
  Interview: "text-interview",
  Offer: "text-offer",
  Rejected: "text-rejected",
  Ghosted: "text-ghosted",
  Undefined: "text-undefined",
};

export function StatusDot({ status, className = "" }: { status: DerivedStatus; className?: string }) {
  return <span className={`inline-block h-2 w-2 shrink-0 rounded-full ${BG[status]} ${className}`} />;
}

export function StatusPill({ status }: { status: DerivedStatus }) {
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 font-mono text-[11px] ${TEXT[status]}`}>
      <StatusDot status={status} />
      {status}
    </span>
  );
}
