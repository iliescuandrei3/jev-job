import { fmtDate, fmtDays, roleLabel } from "@/lib/format";
import type { ApplicationSummary } from "@/lib/types";
import { StatusPill } from "./StatusDot";

/** The "All processes" table. Rows arrive sorted from the API. */
export function ApplicationsTable({
  items,
  onPick,
}: {
  items: ApplicationSummary[];
  onPick: (companyKey: string) => void;
}) {
  return (
    <div className="max-h-[420px] overflow-auto">
      <table className="w-full text-sm">
        <thead className="sticky top-0 bg-card text-left">
          <tr className="eyebrow">
            <th className="py-2 font-normal">Company</th>
            <th className="font-normal">Role</th>
            <th className="font-normal">Applied</th>
            <th className="font-normal">Emails</th>
            <th className="font-normal">Duration</th>
            <th className="font-normal">Status</th>
          </tr>
        </thead>
        <tbody>
          {items.map((a) => (
            <tr
              key={a.id}
              onClick={() => onPick(a.companyKey)}
              className="cursor-pointer border-t hover:bg-accent/50"
            >
              <td className="py-2 font-medium">{a.company}</td>
              <td className="text-muted-foreground">{roleLabel(a.role)}</td>
              <td className="font-mono text-xs">{fmtDate(a.appliedAt)}</td>
              <td className="font-mono text-xs">{a.emailCount}</td>
              <td className="font-mono text-xs">{fmtDays(a.durationDays)}</td>
              <td>
                <StatusPill status={a.status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
