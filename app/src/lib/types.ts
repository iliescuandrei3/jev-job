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
