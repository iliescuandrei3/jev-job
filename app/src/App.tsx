import { useMemo, useState } from "react";
import {
  Activity,
  Building2,
  CalendarClock,
  Flame,
  Ghost,
  MessageSquareReply,
  Repeat,
  Rocket,
  Timer,
  Trophy,
  Zap,
} from "lucide-react";
import { MOCK_EMAILS } from "@/lib/mock-data";
import {
  EMPTY_FILTERS,
  applyFilters,
  buildApplications,
  byCompany,
  dur,
  fmtDate,
  fmtDays,
  insights,
  kpis,
  type Filters,
} from "@/lib/analytics";
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

const ALL_APPS = buildApplications(MOCK_EMAILS);
const ALL_COMPANIES = [...new Set(ALL_APPS.map((a) => a.company))].sort();
const ALL_ROLES = [...new Set(ALL_APPS.map((a) => a.role))].sort();
const pct = (x: number) => `${Math.round(x * 100)}%`;

export default function App() {
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);
  const [focusCompany, setFocusCompany] = useState<string>(byCompany(ALL_APPS)[0]?.company ?? "");
  const apps = useMemo(() => applyFilters(ALL_APPS, filters), [filters]);
  const k = kpis(apps);
  const ins = insights(apps);
  const companies = byCompany(apps);

  const stats = [
    { icon: Rocket, label: "Applications", value: k.total, hint: `${k.active} still open` },
    {
      icon: Building2,
      label: "Companies",
      value: k.companies,
      hint: `${ins.repeat} applied to twice+`,
    },
    {
      icon: MessageSquareReply,
      label: "Response rate",
      value: pct(k.responseRate),
      hint: `median reply ${fmtDays(k.medianReply)}`,
    },
    {
      icon: Activity,
      label: "Interview rate",
      value: pct(k.interviewRate),
      hint: "reached ≥1 interview",
    },
    {
      icon: Trophy,
      label: "Offers",
      value: k.offers,
      hint: `${pct(k.offers / (k.total || 1))} conversion`,
    },
    { icon: Ghost, label: "Ghosted", value: pct(k.ghostRate), hint: "no reply after 21d" },
  ];

  return (
    <main className="mx-auto max-w-7xl space-y-6 px-4 py-8 md:px-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">job hunt telemetry · {MOCK_EMAILS.length} emails parsed</p>
          <h1 className="mt-1 text-4xl font-bold tracking-tight md:text-5xl">
            Pipeline<span className="text-primary">.</span>
          </h1>
        </div>
        <p className="max-w-sm text-sm text-muted-foreground">
          Every recruiting email, turned into processes, funnels and patterns. Filter anything
          below.
        </p>
      </header>

      <SearchBar
        filters={filters}
        onChange={setFilters}
        companies={ALL_COMPANIES}
        roles={ALL_ROLES}
      />

      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
        {stats.map((s, i) => (
          <div
            key={s.label}
            className="panel animate-rise p-4"
            style={{ animationDelay: `${i * 50}ms` }}
          >
            <div className="flex items-center gap-2">
              <s.icon className="h-4 w-4 text-primary" />
              <span className="eyebrow">{s.label}</span>
            </div>
            <div className="mt-3 text-3xl font-bold tabular-nums">{s.value}</div>
            <div className="mt-1 text-xs text-muted-foreground">{s.hint}</div>
          </div>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Panel
          title="Applications over time"
          sub="Weekly, coloured by where each process ended up"
          className="lg:col-span-2"
        >
          <WeeklyChart apps={apps} />
        </Panel>
        <Panel title="Conversion funnel" sub="Stage-to-stage drop-off">
          <Funnel apps={apps} />
        </Panel>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Panel
          title="Application streak map"
          sub="Daily applications, last 26 weeks"
          className="lg:col-span-2"
        >
          <Heatmap apps={apps} />
        </Panel>
        <Panel title="Where things stand" sub="Current status of every process">
          <StatusDonut apps={apps} />
        </Panel>
      </div>

      {/* Insights strip */}
      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
        <Insight
          icon={Zap}
          label="Fastest rejection"
          value={ins.fastest ? fmtDays(dur(ins.fastest)) : "—"}
          detail={ins.fastest ? `${ins.fastest.company} · ${ins.fastest.role}` : "No rejections 🎉"}
        />
        <Insight
          icon={Timer}
          label="Longest process"
          value={ins.longest ? fmtDays(dur(ins.longest)) : "—"}
          detail={ins.longest ? `${ins.longest.company} · ${ins.longest.status}` : ""}
        />
        <Insight
          icon={Flame}
          label="Best streak"
          value={`${ins.best} days`}
          detail={
            ins.busiest ? `Busiest day: ${ins.busiest[1]} apps on ${fmtDate(ins.busiest[0])}` : ""
          }
        />
        <Insight
          icon={CalendarClock}
          label="Best-converting role"
          value={ins.bestRole ? `${ins.bestRole.interviewRate}%` : "—"}
          detail={ins.bestRole ? `${ins.bestRole.role} → interview` : "Need more data"}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel
          title="Process timeline"
          sub="18 most recent processes · ticks are emails · click to inspect"
        >
          <ProcessLanes apps={apps} onPick={setFocusCompany} />
        </Panel>
        <CompanyDeepDive company={focusCompany} onChange={setFocusCompany} />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Panel title="Roles" sub="Volume vs. interview rate (%)">
          <RolesChart apps={apps} />
        </Panel>
        <Panel title="Weekly rhythm" sub="When you apply vs. when they say no">
          <WeekdayChart apps={apps} />
        </Panel>
        <Panel title="Inbox clock" sub="Hour of day replies land (UTC)">
          <HourChart apps={apps} />
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
                  <StatusDot key={a.threadId} status={a.status} />
                ))}
              </span>
            </button>
          ))}
        </div>
      </Panel>

      <Panel title="All processes" sub={`${apps.length} matching`}>
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
              {[...apps]
                .sort((a, b) => b.appliedAt.getTime() - a.appliedAt.getTime())
                .map((a) => (
                  <tr
                    key={a.threadId}
                    onClick={() => setFocusCompany(a.company)}
                    className="cursor-pointer border-t hover:bg-accent/50"
                  >
                    <td className="py-2 font-medium">{a.company}</td>
                    <td className="text-muted-foreground">{a.role}</td>
                    <td className="font-mono text-xs">{fmtDate(a.appliedAt)}</td>
                    <td className="font-mono text-xs">{a.emails.length}</td>
                    <td className="font-mono text-xs">{fmtDays(dur(a))}</td>
                    <td>
                      <StatusPill status={a.status} />
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </Panel>

      <footer className="pb-4 text-center font-mono text-xs text-muted-foreground">
        mock data · wire up your Mongo API in src/lib/mock-data.ts
      </footer>
    </main>
  );
}

function Insight({
  icon: Icon,
  label,
  value,
  detail,
}: {
  icon: typeof Zap;
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="panel relative overflow-hidden p-4">
      <Icon className="absolute -right-2 -top-2 h-16 w-16 text-primary opacity-10" />
      <span className="eyebrow">{label}</span>
      <div className="mt-2 text-2xl font-bold text-primary">{value}</div>
      <div className="mt-1 truncate text-xs text-muted-foreground">{detail}</div>
    </div>
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
              <StatusPill status={a.status} />
            </div>
            <ol className="relative ml-1 space-y-3 border-l pl-4">
              {a.emails.map((e) => (
                <li key={e.emailId} className="relative">
                  <StatusDot
                    status={e.applicationStatus}
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
