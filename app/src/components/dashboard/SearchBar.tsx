import { useMemo, useRef, useState } from "react";
import { Search, X, Building2, Briefcase, CircleDot } from "lucide-react";
import { statusLabel } from "@/lib/status";
import type { DashboardFilters, FilterOptions, Status } from "@/lib/types";
import { StatusDot } from "./StatusDot";

/** `value` is what the filter stores (company key, role, status); `label` is what the user sees. */
type Suggestion = { kind: "company" | "role" | "status"; value: string; label: string };

const NO_OPTIONS: FilterOptions = { companies: [], roles: [], statuses: [] };

export function SearchBar({
  filters,
  onChange,
  options = NO_OPTIONS,
}: {
  filters: DashboardFilters;
  onChange: (f: DashboardFilters) => void;
  /** From GET /dashboard/filters; undefined while loading */
  options?: FilterOptions;
}) {
  const [open, setOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const q = filters.q.toLowerCase().trim();

  const companyNames = useMemo(() => new Map(options.companies.map((c) => [c.key, c.name])), [options.companies]);

  const suggestions = useMemo<Suggestion[]>(() => {
    if (!q) return [];
    const s: Suggestion[] = [];
    // Match the label ("Offer") and the backend value ("accepted")
    options.statuses.filter((x) => (statusLabel(x).toLowerCase().includes(q) || x.includes(q)) && !filters.statuses.includes(x)).forEach((v) =>
      s.push({ kind: "status", value: v, label: statusLabel(v) }),
    );
    options.companies.filter((c) => c.name.toLowerCase().includes(q) && !filters.companies.includes(c.key)).slice(0, 5).forEach((c) =>
      s.push({ kind: "company", value: c.key, label: c.name }),
    );
    options.roles.filter((r) => r.toLowerCase().includes(q) && !filters.roles.includes(r)).slice(0, 4).forEach((v) =>
      s.push({ kind: "role", value: v, label: v }),
    );
    return s;
  }, [q, options, filters]);

  const add = (s: Suggestion) => {
    const next = { ...filters, q: "" };
    if (s.kind === "company") next.companies = [...filters.companies, s.value];
    if (s.kind === "role") next.roles = [...filters.roles, s.value];
    if (s.kind === "status") next.statuses = [...filters.statuses, s.value as Status];
    onChange(next);
    inputRef.current?.focus();
  };

  const chips: (Suggestion & { remove: () => void })[] = [
    ...filters.companies.map((v) => ({ kind: "company" as const, value: v, label: companyNames.get(v) ?? v, remove: () => onChange({ ...filters, companies: filters.companies.filter((x) => x !== v) }) })),
    ...filters.roles.map((v) => ({ kind: "role" as const, value: v, label: v, remove: () => onChange({ ...filters, roles: filters.roles.filter((x) => x !== v) }) })),
    ...filters.statuses.map((v) => ({ kind: "status" as const, value: v, label: statusLabel(v), remove: () => onChange({ ...filters, statuses: filters.statuses.filter((x) => x !== v) }) })),
  ];

  const Icon = ({ kind }: { kind: Suggestion["kind"] }) =>
    kind === "company" ? <Building2 className="h-3.5 w-3.5" /> : kind === "role" ? <Briefcase className="h-3.5 w-3.5" /> : <CircleDot className="h-3.5 w-3.5" />;

  return (
    <div className="relative">
      <div className="panel glow flex flex-wrap items-center gap-2 px-4 py-3 focus-within:ring-1 focus-within:ring-ring">
        <Search className="h-5 w-5 text-primary" />
        {chips.map((c) => (
          <span key={c.kind + c.value} className="inline-flex items-center gap-1.5 rounded-full bg-secondary px-2.5 py-1 text-xs">
            {c.kind === "status" ? <StatusDot status={c.value as Status} /> : <Icon kind={c.kind} />}
            <span className="text-muted-foreground">{c.kind}:</span>
            {c.label}
            <button onClick={c.remove} className="text-muted-foreground hover:text-foreground" aria-label={`Remove ${c.label}`}>
              <X className="h-3 w-3" />
            </button>
          </span>
        ))}
        <input
          ref={inputRef}
          value={filters.q}
          onChange={(e) => onChange({ ...filters, q: e.target.value })}
          onFocus={() => setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 150)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && suggestions[0]) add(suggestions[0]);
            if (e.key === "Backspace" && !filters.q && chips.length) chips[chips.length - 1]!.remove();
          }}
          placeholder={chips.length ? "Add another filter…" : "Search companies, roles, statuses — e.g. “stripe”, “frontend”, “interview”"}
          className="min-w-[200px] flex-1 bg-transparent text-base outline-none placeholder:text-muted-foreground"
        />
        <div className="flex items-center gap-1 rounded-lg bg-secondary p-1 font-mono text-xs">
          {[
            { l: "30d", v: 30 },
            { l: "90d", v: 90 },
            { l: "6m", v: 180 },
            { l: "All", v: null },
          ].map((o) => (
            <button
              key={o.l}
              onClick={() => onChange({ ...filters, rangeDays: o.v })}
              className={`rounded-md px-2 py-1 transition-colors ${filters.rangeDays === o.v ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"}`}
            >
              {o.l}
            </button>
          ))}
        </div>
      </div>
      {open && suggestions.length > 0 && (
        <div className="absolute z-20 mt-2 w-full overflow-hidden rounded-xl border bg-popover p-1 shadow-2xl">
          {suggestions.map((s, i) => (
            <button
              key={s.kind + s.value}
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => add(s)}
              className={`flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-sm hover:bg-accent ${i === 0 ? "bg-accent/60" : ""}`}
            >
              {s.kind === "status" ? <StatusDot status={s.value as Status} /> : <Icon kind={s.kind} />}
              <span>{s.label}</span>
              <span className="eyebrow ml-auto">{s.kind}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
