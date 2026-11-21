import { useState } from "react";
import { fmtRelative } from "@/lib/format";
import { useDashboardFilters } from "@/hooks/use-dashboard-filters";
import { useFilterOptions } from "@/hooks/use-filter-options";
import { useApplications } from "@/hooks/use-applications";
import { useCompanies, useCompany } from "@/hooks/use-companies";
import { useOverview } from "@/hooks/use-overview";
import { usePatterns } from "@/hooks/use-patterns";
import { useTimeline } from "@/hooks/use-timeline";
import { useSyncJob } from "@/hooks/use-sync-job";
import { useSyncStats } from "@/hooks/use-sync-stats";
import { LogoutButton } from "@/components/auth/LogoutButton";
import { ApplicationsTable } from "@/components/dashboard/ApplicationsTable";
import { CompanyGrid } from "@/components/dashboard/CompanyGrid";
import { CompanyHistory, CompanyPicker } from "@/components/dashboard/CompanyHistory";
import { InsightsStrip, StatTiles } from "@/components/dashboard/Overview";
import { PanelState } from "@/components/dashboard/PanelState";
import { SearchBar } from "@/components/dashboard/SearchBar";
import { SyncButton } from "@/components/dashboard/SyncButton";
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
  const companies = useCompanies(queryFilters);
  // A company key. Until something is picked, focus follows the first company in /companies
  const [pickedCompany, setFocusCompany] = useState<string | null>(null);
  const focusCompany = pickedCompany ?? companies.data?.[0]?.key ?? null;
  const company = useCompany(focusCompany);
  const syncStats = useSyncStats();
  const sync = useSyncJob();

  return (
    <main className="mx-auto max-w-7xl space-y-6 px-4 py-8 md:px-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">
            job hunt telemetry
            {syncStats.data && (
              <>
                {" "}
                · {syncStats.data.jobEmails} emails parsed ·{" "}
                {syncStats.data.lastSyncedAt ? `last synced ${fmtRelative(syncStats.data.lastSyncedAt)}` : "never synced"}
              </>
            )}
          </p>
          <h1 className="mt-1 text-4xl font-bold tracking-tight md:text-5xl">
            Pipeline<span className="text-primary">.</span>
          </h1>
        </div>
        <div className="flex flex-col items-end gap-3">
          <div className="flex items-start gap-3">
            <SyncButton
              onSync={sync.start}
              isStarting={sync.isStarting}
              isRunning={sync.isRunning}
              jobState={sync.jobState}
              connectionMessage={sync.connectionMessage}
              error={sync.error}
            />
            <LogoutButton />
          </div>
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
        <Panel title="Company history" sub="Every process you've had with this company">
          <CompanyPicker options={filterOptions.data?.companies ?? []} value={focusCompany} onChange={setFocusCompany} />
          <PanelState
            // A query without a key stays pending; until a key exists, wait for /companies to pick one
            isLoading={focusCompany ? company.isPending : companies.isPending}
            error={company.error}
            isEmpty={!focusCompany}
            emptyText="Pick a company to see its history."
            onRetry={() => void company.refetch()}
          >
            {company.data && <CompanyHistory company={company.data} />}
          </PanelState>
        </Panel>
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
        sub={companies.data ? `${companies.data.length} companies · click one to open its history` : "Click one to open its history"}
      >
        <PanelState
          isLoading={companies.isPending}
          error={companies.error}
          isEmpty={companies.data?.length === 0}
          onRetry={() => void companies.refetch()}
        >
          {companies.data && <CompanyGrid companies={companies.data} selected={focusCompany} onSelect={setFocusCompany} />}
        </PanelState>
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
    </main>
  );
}
