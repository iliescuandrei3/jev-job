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
