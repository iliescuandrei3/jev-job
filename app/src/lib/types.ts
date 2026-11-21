// API types. They mirror the Pydantic schemas in server/schemas/ one-to-one, so change both together.
// Timestamps are ISO 8601 UTC strings.

/** server/schemas/email.py · ApplicationStatus (the status of one email) */
export type ApplicationStatus =
  | "undefined"
  | "applied"
  | "online_assesment"
  | "interview"
  | "accepted"
  | "rejected";

/** server/schemas/application.py · Status (the derived status of an application) */
export type Status = ApplicationStatus | "ghosted";

/** server/schemas/dashboard.py · DashboardFilters (query params of every filtered endpoint) */
export interface DashboardFilters {
  q: string;
  companies: string[]; // companyKeys
  roles: string[];
  /** Applications without a role; OR'd with `roles` */
  unknownRole: boolean;
  statuses: Status[];
  rangeDays: number | null;
}

/** server/schemas/dashboard.py · CompanyOption */
export interface CompanyOption {
  key: string;
  name: string;
}

/** server/schemas/dashboard.py · FilterOptionsOut (GET /dashboard/filters) */
export interface FilterOptions {
  companies: CompanyOption[];
  roles: string[];
  /** Some application has no role (selectable with the `unknownRole` filter) */
  unknownRole: boolean;
  statuses: Status[];
}

/** server/schemas/application.py · ApplicationEmailOut */
export interface ApplicationEmailOut {
  emailId: string;
  date: string;
  applicationStatus: ApplicationStatus;
  title: string;
  description: string;
}

/** server/schemas/application.py · ApplicationOut */
export interface ApplicationOut {
  id: string;
  company: string;
  companyKey: string;
  role: string;
  status: Status;
  appliedAt: string;
  lastAt: string;
  durationDays: number;
  emails: ApplicationEmailOut[];
}

/** server/schemas/application.py · ApplicationSort (`sort` param of GET /applications) */
export type ApplicationSort = "recent" | "duration" | "lastActivity";

/** server/schemas/application.py · ApplicationSummaryOut (a row of GET /applications) */
export interface ApplicationSummary {
  id: string;
  company: string;
  companyKey: string;
  role: string;
  status: Status;
  appliedAt: string;
  lastAt: string;
  durationDays: number;
  emailCount: number;
  emailDates: string[];
}

/** server/schemas/application.py · DateRangeOut */
export interface DateRange {
  start: string;
  end: string;
}

/** server/schemas/application.py · ApplicationListOut (GET /applications) */
export interface ApplicationList {
  total: number;
  /** From the earliest appliedAt of `items` to now: the time axis of the process lanes */
  range: DateRange;
  items: ApplicationSummary[];
}

/** server/schemas/dashboard.py · RoleStatOut */
export interface RoleStat {
  /** "" for applications without a role */
  role: string;
  count: number;
  /** 0–1 */
  interviewRate: number;
}

/** server/schemas/dashboard.py · Weekday */
export type Weekday = "mon" | "tue" | "wed" | "thu" | "fri" | "sat" | "sun";

/** server/schemas/dashboard.py · WeekdayStatOut */
export interface WeekdayStat {
  day: Weekday;
  applied: number;
  rejections: number;
}

/** server/schemas/dashboard.py · HourStatOut */
export interface HourStat {
  /** 0–23, UTC */
  hour: number;
  interview: number;
  rejected: number;
}

/** server/schemas/dashboard.py · PatternsOut (GET /dashboard/patterns) */
export interface PatternsOut {
  /** Top 8 by count */
  roles: RoleStat[];
  /** Mon–Sun */
  weekdays: WeekdayStat[];
  /** Every hour 0–23 */
  hours: HourStat[];
}

/** server/schemas/dashboard.py · KpisOut. Rates are 0–1. */
export interface Kpis {
  applications: number;
  /** applied, online_assesment, interview or undefined */
  open: number;
  companies: number;
  /** Companies with more than one application */
  repeatCompanies: number;
  responseRate: number;
  /** null without any reply */
  medianReplyDays: number | null;
  interviewRate: number;
  offers: number;
  offerRate: number;
  ghostRate: number;
  /** null without any rejection */
  medianRejectionDays: number | null;
}

/** server/schemas/dashboard.py · FunnelStage */
export type FunnelStageName = "applied" | "replied" | "interview" | "offer";

/** server/schemas/dashboard.py · FunnelStageOut */
export interface FunnelStage {
  stage: FunnelStageName;
  value: number;
  /** 0–1 from the previous stage; null for the first */
  conversion: number | null;
}

/** server/schemas/dashboard.py · StatusShareOut */
export interface StatusShare {
  status: Status;
  value: number;
  /** 0–1 of all applications */
  share: number;
}

/** server/schemas/dashboard.py · FastestRejectionOut */
export interface FastestRejection {
  applicationId: string;
  company: string;
  role: string;
  days: number;
}

/** server/schemas/dashboard.py · LongestProcessOut */
export interface LongestProcess {
  applicationId: string;
  company: string;
  status: Status;
  days: number;
}

/** server/schemas/dashboard.py · BusiestDayOut */
export interface BusiestDay {
  /** YYYY-MM-DD, UTC */
  date: string;
  count: number;
}

/** server/schemas/dashboard.py · BestRoleOut */
export interface BestRole {
  role: string;
  /** 0–1 */
  interviewRate: number;
}

/** server/schemas/dashboard.py · InsightsOut */
export interface Insights {
  fastestRejection: FastestRejection | null;
  longestProcess: LongestProcess | null;
  bestStreakDays: number;
  busiestDay: BusiestDay | null;
  /** null unless some role has at least 4 applications */
  bestRole: BestRole | null;
}

/** server/schemas/dashboard.py · OverviewOut (GET /dashboard/overview) */
export interface OverviewOut {
  kpis: Kpis;
  funnel: FunnelStage[];
  statusBreakdown: StatusShare[];
  insights: Insights;
}

/** server/schemas/dashboard.py · WeekCountsOut */
export interface WeekCounts {
  weekStart: string; // YYYY-MM-DD, a Monday (UTC)
  /** Applications applied that week, by current status. Statuses with no application are left out */
  counts: Partial<Record<Status, number>>;
}

/** server/schemas/dashboard.py · HeatmapDayOut */
export interface HeatmapDay {
  date: string; // YYYY-MM-DD (UTC)
  count: number;
}

/** server/schemas/dashboard.py · HeatmapOut */
export interface HeatmapData {
  start: string; // a Monday
  end: string; // today (UTC); no days after it
  /** The busiest day's count; 0 without applications */
  max: number;
  days: HeatmapDay[];
}

/** server/schemas/dashboard.py · TimelineOut (GET /dashboard/timeline) */
export interface TimelineOut {
  weekly: WeekCounts[];
  heatmap: HeatmapData;
}

/** server/routers/auth.py · the session user stored at /auth/callback */
export interface AuthUser {
  sub: string;
  email: string;
  name: string | null;
}

/** server/routers/auth.py · GET /auth/me */
export interface MeResponse {
  user: AuthUser;
  csrf_token: string;
}
