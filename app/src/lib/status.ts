import type { Status } from "./types";

interface StatusMeta {
  label: string;
  /** CSS colour, for inline styles and chart fills */
  color: string;
  /** Tailwind classes, written out in full so Tailwind finds them */
  bg: string;
  text: string;
}

/** Backend status → label and colour. Display only: the API decides which status an application has. */
export const STATUS_META: Record<Status, StatusMeta> = {
  applied: { label: "Applied", color: "var(--status-applied)", bg: "bg-applied", text: "text-applied" },
  online_assesment: {
    label: "Assessment",
    color: "var(--status-assessment)",
    bg: "bg-assessment",
    text: "text-assessment",
  },
  interview: { label: "Interview", color: "var(--status-interview)", bg: "bg-interview", text: "text-interview" },
  // Until the backend has a separate `offer` status (see known-issues.md), `accepted` means an offer
  accepted: { label: "Offer", color: "var(--status-offer)", bg: "bg-offer", text: "text-offer" },
  rejected: { label: "Rejected", color: "var(--status-rejected)", bg: "bg-rejected", text: "text-rejected" },
  ghosted: { label: "Ghosted", color: "var(--status-ghosted)", bg: "bg-ghosted", text: "text-ghosted" },
  undefined: { label: "Undefined", color: "var(--status-undefined)", bg: "bg-undefined", text: "text-undefined" },
};

export const statusLabel = (status: Status) => STATUS_META[status].label;
export const statusColor = (status: Status) => STATUS_META[status].color;
