import {
  Activity,
  Building2,
  CalendarClock,
  Flame,
  Ghost,
  MessageSquareReply,
  Rocket,
  Timer,
  Trophy,
  Zap,
  type LucideIcon,
} from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { fmtDate, fmtDays, pct, roleLabel } from "@/lib/format";
import { statusLabel } from "@/lib/status";
import type { Insights, Kpis } from "@/lib/types";

const daysOrDash = (days: number | null) => (days === null ? "—" : fmtDays(days));

interface Tile {
  icon: LucideIcon;
  label: string;
  value: string | number;
  hint: string;
  /** Explains the label on hover */
  tooltip?: string;
}

/** The six KPI tiles at the top of the dashboard. */
export function StatTiles({ kpis }: { kpis: Kpis }) {
  const tiles: Tile[] = [
    { icon: Rocket, label: "Applications", value: kpis.applications, hint: `${kpis.open} still open` },
    {
      icon: Building2,
      label: "Companies",
      value: kpis.companies,
      hint: `${kpis.repeatCompanies} applied to twice+`,
    },
    {
      icon: MessageSquareReply,
      label: "Response rate",
      value: pct(kpis.responseRate),
      hint: `median reply ${daysOrDash(kpis.medianReplyDays)}`,
    },
    {
      icon: Activity,
      label: "Interview rate",
      value: pct(kpis.interviewRate),
      hint: "reached ≥1 interview",
    },
    { icon: Trophy, label: "Offers", value: kpis.offers, hint: `${pct(kpis.offerRate)} conversion` },
    {
      icon: Ghost,
      label: "Ghosted",
      value: pct(kpis.ghostRate),
      hint: "no reply after 21d",
      tooltip: "no reply after 21 days",
    },
  ];

  return (
    <TooltipProvider delayDuration={200}>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
        {tiles.map((s, i) => (
          <div
            key={s.label}
            className="panel animate-rise p-4"
            style={{ animationDelay: `${i * 50}ms` }}
          >
            <div className="flex items-center gap-2">
              <s.icon className="h-4 w-4 text-primary" />
              {s.tooltip ? (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <span className="eyebrow cursor-help underline decoration-dotted underline-offset-2">
                      {s.label}
                    </span>
                  </TooltipTrigger>
                  <TooltipContent>{s.tooltip}</TooltipContent>
                </Tooltip>
              ) : (
                <span className="eyebrow">{s.label}</span>
              )}
            </div>
            <div className="mt-3 text-3xl font-bold tabular-nums">{s.value}</div>
            <div className="mt-1 text-xs text-muted-foreground">{s.hint}</div>
          </div>
        ))}
      </div>
    </TooltipProvider>
  );
}

/** The four insight cards below the charts. */
export function InsightsStrip({ insights }: { insights: Insights }) {
  const { fastestRejection, longestProcess, bestStreakDays, busiestDay, bestRole } = insights;
  return (
    <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
      <Insight
        icon={Zap}
        label="Fastest rejection"
        value={fastestRejection ? fmtDays(fastestRejection.days) : "—"}
        detail={
          fastestRejection
            ? `${fastestRejection.company} · ${roleLabel(fastestRejection.role)}`
            : "No rejections 🎉"
        }
      />
      <Insight
        icon={Timer}
        label="Longest process"
        value={longestProcess ? fmtDays(longestProcess.days) : "—"}
        detail={longestProcess ? `${longestProcess.company} · ${statusLabel(longestProcess.status)}` : ""}
      />
      <Insight
        icon={Flame}
        label="Best streak"
        value={`${bestStreakDays} ${bestStreakDays === 1 ? "day" : "days"}`}
        detail={busiestDay ? `Busiest day: ${busiestDay.count} apps on ${fmtDate(busiestDay.date)}` : ""}
      />
      <Insight
        icon={CalendarClock}
        label="Best-converting role"
        value={bestRole ? pct(bestRole.interviewRate) : "—"}
        detail={bestRole ? `${bestRole.role} → interview` : "Need more data"}
      />
    </div>
  );
}

function Insight({
  icon: Icon,
  label,
  value,
  detail,
}: {
  icon: LucideIcon;
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
