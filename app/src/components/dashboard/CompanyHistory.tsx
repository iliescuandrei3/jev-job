import { Repeat } from "lucide-react";
import { fmtDate, roleLabel } from "@/lib/format";
import type { CompanyDetailOut, CompanyOption } from "@/lib/types";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { StatusDot, StatusPill } from "./StatusDot";

/** Picker for the company history panel. Options come from /dashboard/filters (every company). */
export function CompanyPicker({
  options,
  value,
  onChange,
}: {
  options: CompanyOption[];
  value: string | null;
  onChange: (companyKey: string) => void;
}) {
  return (
    <Select value={value ?? undefined} onValueChange={onChange}>
      <SelectTrigger className="mb-4 bg-secondary" aria-label="Company">
        <SelectValue placeholder="Pick a company" />
      </SelectTrigger>
      <SelectContent>
        {options.map((option) => (
          <SelectItem key={option.key} value={option.key}>
            {option.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

/** Every process with one company. Email titles and descriptions are server templates, never real email text. */
export function CompanyHistory({ company }: { company: CompanyDetailOut }) {
  return (
    <>
      <div className="mb-4 flex gap-6 text-sm">
        <div>
          <div className="text-2xl font-bold">{company.applicationCount}</div>
          <div className="eyebrow">processes</div>
        </div>
        <div>
          <div className="text-2xl font-bold">{company.emailCount}</div>
          <div className="eyebrow">emails</div>
        </div>
        <div className="flex items-center gap-2">
          <Repeat className="h-4 w-4 text-primary" />
          <span className="text-xs text-muted-foreground">{company.repeat ? "Repeat applicant" : "First contact"}</span>
        </div>
      </div>
      <div className="max-h-[340px] space-y-5 overflow-auto pr-2">
        {company.applications.map((a) => (
          <div key={a.id}>
            <div className="mb-2 flex items-center justify-between">
              <span className="text-sm font-medium">{roleLabel(a.role)}</span>
              <StatusPill status={a.status} />
            </div>
            <ol className="relative ml-1 space-y-3 border-l pl-4">
              {a.emails.map((e) => (
                <li key={e.emailId} className="relative">
                  <StatusDot status={e.applicationStatus} className="absolute -left-[21px] top-1.5 ring-4 ring-card" />
                  <div className="flex items-baseline justify-between gap-2">
                    <span className="truncate text-xs font-medium">{e.title}</span>
                    <span className="shrink-0 font-mono text-[10px] text-muted-foreground">{fmtDate(e.date)}</span>
                  </div>
                  <p className="truncate text-xs text-muted-foreground">{e.description}</p>
                </li>
              ))}
            </ol>
          </div>
        ))}
      </div>
    </>
  );
}
