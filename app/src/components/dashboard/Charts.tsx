import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import {
  STATUSES, fromMockStatus, funnel, heatmap, statusBreakdown, weekly,
  type Application,
} from "@/lib/analytics";
import { fmtDate, fmtWeekday, roleLabel } from "@/lib/format";
import { statusColor, statusLabel } from "@/lib/status";
import type { ApplicationSummary, DateRange, HourStat, RoleStat, WeekdayStat } from "@/lib/types";
import { StatusDot } from "./StatusDot";

const axis = { stroke: "var(--muted-foreground)", fontSize: 11, tickLine: false, axisLine: false } as const;
const tooltip = {
  contentStyle: { background: "var(--popover)", border: "1px solid var(--border)", borderRadius: 10, fontSize: 12 },
  labelStyle: { color: "var(--foreground)" },
  cursor: { fill: "color-mix(in oklab, var(--foreground) 6%, transparent)" },
};

export function Panel({ title, sub, children, className = "" }: { title: string; sub?: string; children: React.ReactNode; className?: string }) {
  return (
    <section className={`panel animate-rise p-5 ${className}`}>
      <header className="mb-4">
        <h3 className="text-sm font-semibold">{title}</h3>
        {sub && <p className="text-xs text-muted-foreground">{sub}</p>}
      </header>
      {children}
    </section>
  );
}

export function Funnel({ apps }: { apps: Application[] }) {
  const data = funnel(apps);
  const max = data[0]!.value || 1;
  return (
    <div className="space-y-3">
      {data.map((d, i) => (
        <div key={d.stage}>
          <div className="mb-1 flex justify-between text-xs">
            <span>{d.stage}</span>
            <span className="font-mono text-muted-foreground">
              {d.value}
              {i > 0 && <span className="ml-2 text-primary">{Math.round((d.value / (data[i - 1]!.value || 1)) * 100)}%</span>}
            </span>
          </div>
          <div className="h-7 overflow-hidden rounded-md bg-secondary">
            <div
              className="h-full rounded-md bg-primary transition-all duration-700"
              style={{ width: `${(d.value / max) * 100}%`, opacity: 1 - i * 0.18 }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

export function WeeklyChart({ apps }: { apps: Application[] }) {
  const data = weekly(apps);
  return (
    <ResponsiveContainer width="100%" height={240}>
      <AreaChart data={data} margin={{ left: -20, right: 4 }}>
        <CartesianGrid stroke="var(--border)" vertical={false} />
        <XAxis dataKey="week" {...axis} interval={3} />
        <YAxis {...axis} allowDecimals={false} />
        <Tooltip {...tooltip} />
        {STATUSES.map((s) => (
          <Area key={s} type="monotone" dataKey={s} stackId="1" stroke={statusColor(fromMockStatus(s))} fill={statusColor(fromMockStatus(s))} fillOpacity={0.35} />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function StatusDonut({ apps }: { apps: Application[] }) {
  const data = statusBreakdown(apps);
  const total = apps.length;
  return (
    <div className="flex items-center gap-4">
      <div className="relative h-44 w-44 shrink-0">
        <ResponsiveContainer>
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="status" innerRadius={55} outerRadius={80} paddingAngle={2} stroke="none">
              {data.map((d) => <Cell key={d.status} fill={statusColor(fromMockStatus(d.status))} />)}
            </Pie>
            <Tooltip {...tooltip} />
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-bold">{total}</span>
          <span className="eyebrow">processes</span>
        </div>
      </div>
      <ul className="flex-1 space-y-2 text-sm">
        {data.map((d) => (
          <li key={d.status} className="flex items-center gap-2">
            <StatusDot status={fromMockStatus(d.status)} />
            {statusLabel(fromMockStatus(d.status))}
            <span className="ml-auto font-mono text-muted-foreground">{Math.round((d.value / (total || 1)) * 100)}%</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function Heatmap({ apps }: { apps: Application[] }) {
  const cols = heatmap(apps);
  const max = Math.max(1, ...cols.flat().map((c) => c.count));
  return (
    <div className="overflow-x-auto">
      <div className="flex gap-[3px]">
        {cols.map((col, i) => (
          <div key={i} className="flex flex-col gap-[3px]">
            {col.map((c) => (
              <div
                key={c.date}
                title={c.count >= 0 ? `${c.date}: ${c.count} applications` : ""}
                className="h-3.5 w-3.5 rounded-[3px] bg-secondary"
                style={
                  c.count > 0
                    ? { background: `color-mix(in oklab, var(--primary) ${25 + (c.count / max) * 75}%, var(--secondary))` }
                    : c.count < 0
                      ? { opacity: 0 }
                      : undefined
                }
              />
            ))}
          </div>
        ))}
      </div>
      <div className="mt-3 flex items-center gap-2 text-[11px] text-muted-foreground">
        less
        {[0, 0.33, 0.66, 1].map((p) => (
          <span key={p} className="h-3 w-3 rounded-[3px]" style={{ background: `color-mix(in oklab, var(--primary) ${p * 100}%, var(--secondary))` }} />
        ))}
        more
      </div>
    </div>
  );
}

export function RolesChart({ roles }: { roles: RoleStat[] }) {
  // Bars share one axis, so the 0–1 rate is drawn as a whole percentage
  const data = roles.map((r) => ({ role: roleLabel(r.role), count: r.count, interviewRate: Math.round(r.interviewRate * 100) }));
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} layout="vertical" margin={{ left: 40, right: 10 }}>
        <XAxis type="number" {...axis} hide />
        <YAxis type="category" dataKey="role" {...axis} width={120} />
        <Tooltip {...tooltip} formatter={(v, n) => (n === "interviewRate" ? [`${v}%`, "Interview rate"] : [v, "Applications"])} />
        <Bar dataKey="count" fill="var(--status-applied)" radius={[0, 4, 4, 0]} barSize={10} />
        <Bar dataKey="interviewRate" fill="var(--status-interview)" radius={[0, 4, 4, 0]} barSize={10} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function WeekdayChart({ weekdays }: { weekdays: WeekdayStat[] }) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={weekdays} margin={{ left: -24 }}>
        <XAxis dataKey="day" {...axis} tickFormatter={fmtWeekday} />
        <YAxis {...axis} allowDecimals={false} />
        <Tooltip {...tooltip} labelFormatter={(d) => fmtWeekday(String(d))} />
        <Bar dataKey="applied" name="Applications sent" fill="var(--primary)" radius={4} />
        <Bar dataKey="rejections" name="Rejections received" fill="var(--status-rejected)" radius={4} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function HourChart({ hours }: { hours: HourStat[] }) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={hours} margin={{ left: -24 }}>
        <XAxis dataKey="hour" {...axis} interval={2} tickFormatter={(h) => `${h}h`} />
        <YAxis {...axis} allowDecimals={false} />
        <Tooltip {...tooltip} labelFormatter={(h) => `${h}:00 – ${h}:59`} />
        <Bar dataKey="interview" name="Interview" stackId="a" fill="var(--status-interview)" />
        <Bar dataKey="rejected" name="Rejected" stackId="a" fill="var(--status-rejected)" radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

/** Gantt-style lanes: each process from first to last email. */
export function ProcessLanes({
  items,
  range,
  onPick,
}: {
  items: ApplicationSummary[];
  range: DateRange;
  onPick: (company: string) => void;
}) {
  const start = new Date(range.start).getTime();
  const span = new Date(range.end).getTime() - start || 1;
  const pos = (date: string) => ((new Date(date).getTime() - start) / span) * 100;
  return (
    <div className="space-y-1.5">
      {items.map((a) => {
        const left = pos(a.appliedAt);
        const width = Math.max(1.2, pos(a.lastAt) - left);
        return (
          <button key={a.id} onClick={() => onPick(a.company)} className="group grid w-full grid-cols-[150px_1fr] items-center gap-3 text-left">
            <span className="truncate text-xs">
              <span className="font-medium group-hover:text-primary">{a.company}</span>
              {a.role && <span className="text-muted-foreground"> · {a.role.split(" ")[0]}</span>}
            </span>
            <div className="relative h-5 rounded bg-secondary/50">
              <div
                className="absolute top-1/2 h-2.5 -translate-y-1/2 rounded-full"
                style={{ left: `${left}%`, width: `${width}%`, background: statusColor(a.status) }}
              />
              {a.emailDates.map((date, i) => (
                <span
                  key={`${date}-${i}`}
                  className="absolute top-1/2 h-3.5 w-0.5 -translate-y-1/2 rounded bg-foreground/70"
                  style={{ left: `${pos(date)}%` }}
                />
              ))}
            </div>
          </button>
        );
      })}
      <div className="grid grid-cols-[150px_1fr] gap-3 pt-1 font-mono text-[10px] text-muted-foreground">
        <span />
        <div className="flex justify-between">
          <span>{fmtDate(range.start)}</span>
          <span>today</span>
        </div>
      </div>
    </div>
  );
}
