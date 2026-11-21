import type { CompanyOut } from "@/lib/types";
import { StatusDot } from "./StatusDot";

const GRID_SIZE = 24;

/** The companies grid: the first 24 companies as the API sorted them, one status dot per application. */
export function CompanyGrid({
  companies,
  selected,
  onSelect,
}: {
  companies: CompanyOut[];
  selected: string | null;
  onSelect: (companyKey: string) => void;
}) {
  return (
    <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
      {companies.slice(0, GRID_SIZE).map((company) => (
        <button
          key={company.key}
          onClick={() => onSelect(company.key)}
          className={`flex items-center gap-3 rounded-lg border px-3 py-2 text-left transition-colors hover:border-primary ${selected === company.key ? "border-primary bg-accent" : ""}`}
        >
          <span className="flex h-8 w-8 items-center justify-center rounded-md bg-secondary font-mono text-xs">
            {company.name.slice(0, 2)}
          </span>
          <span className="flex-1 truncate text-sm">{company.name}</span>
          <span className="flex gap-1">
            {company.statuses.map((status, i) => (
              <StatusDot key={i} status={status} />
            ))}
          </span>
        </button>
      ))}
    </div>
  );
}
