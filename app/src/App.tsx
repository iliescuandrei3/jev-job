import { useState } from "react";
import { Repeat } from "lucide-react";
import { MOCK_EMAILS } from "@/lib/mock-data";
import { buildApplications, byCompany, fromMockStatus } from "@/lib/analytics";
import { fmtDate } from "@/lib/format";
import { useDashboardFilters } from "@/hooks/use-dashboard-filters";
import { useFilterOptions } from "@/hooks/use-filter-options";
import { useApplications } from "@/hooks/use-applications";
import { useOverview } from "@/hooks/use-overview";
import { usePatterns } from "@/hooks/use-patterns";
import { useTimeline } from "@/hooks/use-timeline";
import { LogoutButton } from "@/components/auth/LogoutButton";
import { ApplicationsTable } from "@/components/dashboard/ApplicationsTable";
import { InsightsStrip, StatTiles } from "@/components/dashboard/Overview";
import { PanelState } from "@/components/dashboard/PanelState";
import { SearchBar } from "@/components/dashboard/SearchBar";
import { StatusDot, StatusPill } from "@/components/dashboard/StatusDot";
import {
  Funnel,
  Heatmap,
  HourChart,
  Panel,
  ProcessLanes,
  RolesChart,
  StatusDonut,
  WeekdayChart,
  WeeklyChart,
} from "@/components/dashboard/Charts";
import { Skeleton } from "@/components/ui/skeleton";

const ALL_APPS = buildApplications(MOCK_EMAILS);
const ALL_COMPANIES = [...new Set(ALL_APPS.map((a) => a.company))].sort();
const LANE_COUNT = 18;
const TIMELINE_WEEKS = 26;

export default function App() {
  const { filters, setFilters, queryFilters } = useDashboardFilters();
  const filterOptions = useFilterOptions();
  const applications = useApplications(queryFilters, { sort: "recent" });
  const lanes = useApplications(queryFilters, { sort: "recent", limit: LANE_COUNT });
  const patterns = usePatterns(queryFilters);
  const overview = useOverview(queryFilters);
  const timeline = useTimeline(queryFilters, TIMELINE_WEEKS);
  const [focusCompany, setFocusCompany] = useState<string>(byCompany(ALL_APPS)[0]?.company ?? "");
  // Widgets still read mock data and ignore the filters until their vertical task (04–09)
  const apps = ALL_APPS;
  const companies = byCompany(apps);

  return (
    <main className="mx-auto max-w-7xl space-y-6 px-4 py-8 md:px-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">job hunt telemetry · {MOCK_EMAILS.length} emails parsed</p>
          <h1 className="mt-1 text-4xl font-bold tracking-tight md:text-5xl">
            Pipeline<span className="text-primary">.</span>
          </h1>
        </div>
        <div className="flex flex-col items-end gap-3">
          <LogoutButton />
          <p className="max-w-sm text-right text-sm text-muted-foreground">
            Every recruiting email, turned into processes, funnels and patterns. Filter anything
            below.
          </p>
        </div>
      </header>

      <SearchBar filters={filters} onChange={setFilters} options={filterOptions.data} />

      <PanelState
        isLoading={overview.isPending}
        error={overview.error}
        onRetry={() => void overview.refetch()}
        skeleton={
          <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
            {Array.from({ length: 6 }, (_, i) => (
              <Skeleton key={i} className="h-[108px] rounded-xl" />
            ))}
          </div>
        }
      >
        {overview.data && <StatTiles kpis={overview.data.kpis} />}
      </PanelState>

      <div className="grid gap-4 lg:grid-cols-3">
        <Panel
          title="Applications over time"
          sub="Weekly, coloured by where each process ended up"
          className="lg:col-span-2"
        >
          <PanelState
            isLoading={timeline.isPending}
            error={timeline.error}
            isEmpty={timeline.data?.heatmap.max === 0}
            onRetry={() => void timeline.refetch()}
            skeleton={<Skeleton className="h-[240px] w-full" />}
          >
            {timeline.data && <WeeklyChart weeks={timeline.data.weekly} />}
          </PanelState>
        </Panel>
        <Panel title="Conversion funnel" sub="Stage-to-stage drop-off">
          <PanelState
            isLoading={overview.isPending}
            error={overview.error}
            isEmpty={overview.data?.kpis.applications === 0}
            onRetry={() => void overview.refetch()}
          >
            {overview.data && <Funnel stages={overview.data.funnel} />}
          </PanelState>
        </Panel>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Panel
          title="Application streak map"
          sub={`Daily applications, last ${TIMELINE_WEEKS} weeks`}
          className="lg:col-span-2"
        >
          <PanelState
            isLoading={timeline.isPending}
            error={timeline.error}
            isEmpty={timeline.data?.heatmap.max === 0}
            onRetry={() => void timeline.refetch()}
          >
            {timeline.data && <Heatmap data={timeline.data.heatmap} />}
          </PanelState>
        </Panel>
        <Panel title="Where things stand" sub="Current status of every process">
          <PanelState
            isLoading={overview.isPending}
            error={overview.error}
            isEmpty={overview.data?.statusBreakdown.length === 0}
            onRetry={() => void overview.refetch()}
          >
            {overview.data && (
              <StatusDonut data={overview.data.statusBreakdown} total={overview.data.kpis.applications} />
            )}
          </PanelState>
        </Panel>
      </div>

      {/* Insights strip */}
      <PanelState
        isLoading={overview.isPending}
        error={overview.error}
        onRetry={() => void overview.refetch()}
        skeleton={
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 4 }, (_, i) => (
              <Skeleton key={i} className="h-[92px] rounded-xl" />
            ))}
          </div>
        }
      >
        {overview.data && <InsightsStrip insights={overview.data.insights} />}
      </PanelState>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel
          title="Process timeline"
          sub={`${LANE_COUNT} most recent processes · ticks are emails · click to inspect`}
        >
          <PanelState
            isLoading={lanes.isPending}
            error={lanes.error}
            isEmpty={lanes.data?.items.length === 0}
            emptyText="No processes match."
            onRetry={() => void lanes.refetch()}
          >
            {lanes.data && (
              <ProcessLanes items={lanes.data.items} range={lanes.data.range} onPick={setFocusCompany} />
            )}
          </PanelState>
        </Panel>
        <CompanyDeepDive company={focusCompany} onChange={setFocusCompany} />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Panel title="Roles" sub="Volume vs. interview rate (%)">
          <PanelState
            isLoading={patterns.isPending}
            error={patterns.error}
            isEmpty={patterns.data?.roles.length === 0}
            onRetry={() => void patterns.refetch()}
          >
            {patterns.data && <RolesChart roles={patterns.data.roles} />}
          </PanelState>
        </Panel>
        <Panel title="Weekly rhythm" sub="When you apply vs. when they say no">
          <PanelState isLoading={patterns.isPending} error={patterns.error} onRetry={() => void patterns.refetch()}>
            {patterns.data && <WeekdayChart weekdays={patterns.data.weekdays} />}
          </PanelState>
        </Panel>
        <Panel title="Inbox clock" sub="Hour of day replies land (UTC)">
          <PanelState isLoading={patterns.isPending} error={patterns.error} onRetry={() => void patterns.refetch()}>
            {patterns.data && <HourChart hours={patterns.data.hours} />}
          </PanelState>
        </Panel>
      </div>

      <Panel
        title="Companies"
        sub={`${companies.length} companies · click one to open its history`}
      >
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          {companies.slice(0, 24).map(({ company, list }) => (
            <button
              key={company}
              onClick={() => setFocusCompany(company)}
              className={`flex items-center gap-3 rounded-lg border px-3 py-2 text-left transition-colors hover:border-primary ${focusCompany === company ? "border-primary bg-accent" : ""}`}
            >
              <span className="flex h-8 w-8 items-center justify-center rounded-md bg-secondary font-mono text-xs">
                {company.slice(0, 2)}
              </span>
              <span className="flex-1 truncate text-sm">{company}</span>
              <span className="flex gap-1">
                {list.map((a) => (
                  <StatusDot key={a.threadId} status={fromMockStatus(a.status)} />
                ))}
              </span>
            </button>
          ))}
        </div>
      </Panel>

      <Panel
        title="All processes"
        sub={applications.data ? `${applications.data.total} matching` : "Every process, newest first"}
      >
        <PanelState
          isLoading={applications.isPending}
          error={applications.error}
          isEmpty={applications.data?.items.length === 0}
          onRetry={() => void applications.refetch()}
        >
          {applications.data && <ApplicationsTable items={applications.data.items} onPick={setFocusCompany} />}
        </PanelState>
      </Panel>

      <footer className="pb-4 text-center font-mono text-xs text-muted-foreground">
        mock data · wire up your Mongo API in src/lib/mock-data.ts
      </footer>
    </main>
  );
}

function CompanyDeepDive({
  company,
  onChange,
}: {
  company: string;
  onChange: (c: string) => void;
}) {
  const list = ALL_APPS.filter((a) => a.company === company).sort(
    (a, b) => b.appliedAt.getTime() - a.appliedAt.getTime(),
  );
  return (
    <Panel title="Company history" sub="Every process you've had with this company">
      <select
        value={company}
        onChange={(e) => onChange(e.target.value)}
        className="mb-4 w-full rounded-lg border bg-secondary px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-ring"
      >
        {ALL_COMPANIES.map((c) => (
          <option key={c}>{c}</option>
        ))}
      </select>
      <div className="mb-4 flex gap-6 text-sm">
        <div>
          <div className="text-2xl font-bold">{list.length}</div>
          <div className="eyebrow">processes</div>
        </div>
        <div>
          <div className="text-2xl font-bold">{list.reduce((n, a) => n + a.emails.length, 0)}</div>
          <div className="eyebrow">emails</div>
        </div>
        <div className="flex items-center gap-2">
          <Repeat className="h-4 w-4 text-primary" />
          <span className="text-xs text-muted-foreground">
            {list.length > 1 ? "Repeat applicant" : "First contact"}
          </span>
        </div>
      </div>
      <div className="max-h-[340px] space-y-5 overflow-auto pr-2">
        {list.map((a) => (
          <div key={a.threadId}>
            <div className="mb-2 flex items-center justify-between">
              <span className="text-sm font-medium">{a.role}</span>
              <StatusPill status={fromMockStatus(a.status)} />
            </div>
            <ol className="relative ml-1 space-y-3 border-l pl-4">
              {a.emails.map((e) => (
                <li key={e.emailId} className="relative">
                  <StatusDot
                    status={fromMockStatus(e.applicationStatus)}
                    className="absolute -left-[21px] top-1.5 ring-4 ring-card"
                  />
                  <div className="flex items-baseline justify-between gap-2">
                    <span className="truncate text-xs font-medium">{e.subject}</span>
                    <span className="shrink-0 font-mono text-[10px] text-muted-foreground">
                      {fmtDate(e.date)}
                    </span>
                  </div>
                  <p className="truncate text-xs text-muted-foreground">{e.snippet}</p>
                </li>
              ))}
            </ol>
          </div>
        ))}
      </div>
    </Panel>
  );
}
