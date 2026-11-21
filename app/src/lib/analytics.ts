import type { ApplicationStatus, Email } from "./mock-data";
import { NOW } from "./mock-data";
import type { Status } from "./types";

const DAY = 86_400_000;
export const GHOST_AFTER_DAYS = 21;

export type DerivedStatus = ApplicationStatus | "Ghosted";

/** Temporary bridge: mock statuses → backend statuses, for widgets still on mock data. Goes away in task 10. */
const MOCK_TO_STATUS: Record<DerivedStatus, Status> = {
  Applied: "applied",
  Interview: "interview",
  Offer: "accepted",
  Rejected: "rejected",
  Ghosted: "ghosted",
  Undefined: "undefined",
};
export const fromMockStatus = (status: DerivedStatus): Status => MOCK_TO_STATUS[status];

export interface Application {
  threadId: string;
  company: string;
  role: string;
  emails: Email[];
  appliedAt: Date;
  lastAt: Date;
  status: DerivedStatus;
  reachedInterview: boolean;
  firstReplyDays: number | null;
}

/** Group emails by thread into application processes. */
export function buildApplications(emails: Email[]): Application[] {
  const map = new Map<string, Email[]>();
  for (const e of emails) {
    const arr = map.get(e.threadId) ?? [];
    arr.push(e);
    map.set(e.threadId, arr);
  }
  return [...map.values()].map((list) => {
    const sorted = [...list].sort((a, b) => a.date.localeCompare(b.date));
    const first = sorted[0]!;
    const last = sorted[sorted.length - 1]!;
    const appliedAt = new Date(first.date);
    const lastAt = new Date(last.date);
    const reply = sorted.find((e) => e.applicationStatus !== "Applied");
    let status: DerivedStatus = last.applicationStatus;
    if (status === "Applied" && (NOW.getTime() - lastAt.getTime()) / DAY > GHOST_AFTER_DAYS) status = "Ghosted";
    return {
      threadId: first.threadId,
      company: first.company,
      role: first.role,
      emails: sorted,
      appliedAt,
      lastAt,
      status,
      reachedInterview: sorted.some((e) => e.applicationStatus === "Interview" || e.applicationStatus === "Offer"),
      firstReplyDays: reply ? (new Date(reply.date).getTime() - appliedAt.getTime()) / DAY : null,
    };
  });
}

export interface Filters {
  text: string;
  companies: string[];
  roles: string[];
  statuses: DerivedStatus[];
  rangeDays: number | null;
}

export const EMPTY_FILTERS: Filters = { text: "", companies: [], roles: [], statuses: [], rangeDays: null };

export function applyFilters(apps: Application[], f: Filters) {
  const q = f.text.trim().toLowerCase();
  return apps.filter((a) => {
    if (f.companies.length && !f.companies.includes(a.company)) return false;
    if (f.roles.length && !f.roles.includes(a.role)) return false;
    if (f.statuses.length && !f.statuses.includes(a.status)) return false;
    if (f.rangeDays && NOW.getTime() - a.appliedAt.getTime() > f.rangeDays * DAY) return false;
    if (q && !`${a.company} ${a.role} ${a.emails.map((e) => e.subject).join(" ")}`.toLowerCase().includes(q)) return false;
    return true;
  });
}

const median = (xs: number[]) => {
  if (!xs.length) return 0;
  const s = [...xs].sort((a, b) => a - b);
  const m = Math.floor(s.length / 2);
  return s.length % 2 ? s[m]! : (s[m - 1]! + s[m]!) / 2;
};

export function kpis(apps: Application[]) {
  const n = apps.length || 1;
  const replied = apps.filter((a) => a.firstReplyDays !== null);
  const rejDays = apps
    .filter((a) => a.status === "Rejected")
    .map((a) => (a.lastAt.getTime() - a.appliedAt.getTime()) / DAY);
  return {
    total: apps.length,
    companies: new Set(apps.map((a) => a.company)).size,
    responseRate: replied.length / n,
    interviewRate: apps.filter((a) => a.reachedInterview).length / n,
    offers: apps.filter((a) => a.status === "Offer").length,
    ghostRate: apps.filter((a) => a.status === "Ghosted").length / n,
    medianReply: median(replied.map((a) => a.firstReplyDays!)),
    medianRejection: median(rejDays),
    active: apps.filter((a) => a.status === "Interview" || a.status === "Applied" || a.status === "Undefined").length,
  };
}

export function funnel(apps: Application[]) {
  return [
    { stage: "Applied", value: apps.length },
    { stage: "Got a reply", value: apps.filter((a) => a.firstReplyDays !== null).length },
    { stage: "Interview", value: apps.filter((a) => a.reachedInterview).length },
    { stage: "Offer", value: apps.filter((a) => a.status === "Offer").length },
  ];
}

export const STATUSES: DerivedStatus[] = ["Applied", "Interview", "Offer", "Rejected", "Ghosted", "Undefined"];

export function weekly(apps: Application[], weeks = 26) {
  const start = NOW.getTime() - weeks * 7 * DAY;
  const rows = Array.from({ length: weeks }, (_, i) => {
    const d = new Date(start + i * 7 * DAY);
    const row: Record<string, number | string> = { week: `${d.getUTCDate()}/${d.getUTCMonth() + 1}` };
    STATUSES.forEach((s) => (row[s] = 0));
    return row;
  });
  for (const a of apps) {
    const i = Math.floor((a.appliedAt.getTime() - start) / (7 * DAY));
    if (i >= 0 && i < weeks) (rows[i]![a.status] as number)++;
  }
  return rows;
}

export function statusBreakdown(apps: Application[]) {
  return STATUSES.map((s) => ({ status: s, value: apps.filter((a) => a.status === s).length })).filter((x) => x.value);
}

export function byCompany(apps: Application[]) {
  const m = new Map<string, Application[]>();
  apps.forEach((a) => m.set(a.company, [...(m.get(a.company) ?? []), a]));
  return [...m.entries()].map(([company, list]) => ({ company, list })).sort((a, b) => b.list.length - a.list.length);
}

export function byRole(apps: Application[]) {
  const m = new Map<string, Application[]>();
  apps.forEach((a) => m.set(a.role, [...(m.get(a.role) ?? []), a]));
  return [...m.entries()]
    .map(([role, list]) => ({
      role,
      count: list.length,
      interviewRate: Math.round((list.filter((a) => a.reachedInterview).length / list.length) * 100),
    }))
    .sort((a, b) => b.count - a.count);
}

const WD = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
export function weekdayPattern(apps: Application[]) {
  const rows = WD.map((d) => ({ day: d, sent: 0, rejections: 0 }));
  for (const a of apps) {
    rows[(a.appliedAt.getUTCDay() + 6) % 7].sent++;
    a.emails
      .filter((e) => e.applicationStatus === "Rejected")
      .forEach((e) => rows[(new Date(e.date).getUTCDay() + 6) % 7].rejections++);
  }
  return rows;
}

export function hourPattern(apps: Application[]) {
  const rows = Array.from({ length: 24 }, (_, h) => ({ hour: h, Rejected: 0, Interview: 0 }));
  apps.forEach((a) =>
    a.emails.forEach((e) => {
      if (e.applicationStatus === "Rejected" || e.applicationStatus === "Interview")
        rows[new Date(e.date).getUTCHours()][e.applicationStatus]++;
    }),
  );
  return rows;
}

export function heatmap(apps: Application[], weeks = 26) {
  const counts = new Map<string, number>();
  apps.forEach((a) => {
    const k = a.appliedAt.toISOString().slice(0, 10);
    counts.set(k, (counts.get(k) ?? 0) + 1);
  });
  const end = new Date(NOW);
  const startOffset = (end.getUTCDay() + 6) % 7;
  const start = new Date(end.getTime() - ((weeks - 1) * 7 + startOffset) * DAY);
  const cols: { date: string; count: number }[][] = [];
  for (let w = 0; w < weeks; w++) {
    const col = [];
    for (let d = 0; d < 7; d++) {
      const date = new Date(start.getTime() + (w * 7 + d) * DAY);
      const k = date.toISOString().slice(0, 10);
      col.push({ date: k, count: date > end ? -1 : counts.get(k) ?? 0 });
    }
    cols.push(col);
  }
  return cols;
}

export function insights(apps: Application[]) {
  const rejected = apps.filter((a) => a.status === "Rejected");
  const fastest = [...rejected].sort(
    (a, b) => a.lastAt.getTime() - a.appliedAt.getTime() - (b.lastAt.getTime() - b.appliedAt.getTime()),
  )[0];
  const longest = [...apps].sort(
    (a, b) => b.lastAt.getTime() - b.appliedAt.getTime() - (a.lastAt.getTime() - a.appliedAt.getTime()),
  )[0];
  const days = [...new Set(apps.map((a) => a.appliedAt.toISOString().slice(0, 10)))].sort();
  let streak = 0, best = 0, prev = 0;
  for (const d of days) {
    const t = new Date(d).getTime();
    streak = t - prev === DAY ? streak + 1 : 1;
    best = Math.max(best, streak);
    prev = t;
  }
  const roles = byRole(apps).filter((r) => r.count >= 4);
  const bestRole = [...roles].sort((a, b) => b.interviewRate - a.interviewRate)[0];
  const repeat = byCompany(apps).filter((c) => c.list.length > 1).length;
  const dayCounts = new Map<string, number>();
  apps.forEach((a) => {
    const k = a.appliedAt.toISOString().slice(0, 10);
    dayCounts.set(k, (dayCounts.get(k) ?? 0) + 1);
  });
  const busiest = [...dayCounts.entries()].sort((a, b) => b[1] - a[1])[0];
  return { fastest, longest, best, bestRole, repeat, busiest };
}

export const dur = (a: Application) => (a.lastAt.getTime() - a.appliedAt.getTime()) / DAY;
