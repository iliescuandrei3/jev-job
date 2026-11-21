// Display formatters. Formatting only: every number comes from the API.

/** Days as `12d`, or hours (`5h`) when under a day. */
export const fmtDays = (d: number) => (d < 1 ? `${Math.max(1, Math.round(d * 24))}h` : `${Math.round(d)}d`);

/** `14 Sept 26`, always in UTC. */
export const fmtDate = (d: Date | string) =>
  new Date(d).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "2-digit", timeZone: "UTC" });

/** `2026-05-04` → `4/5`, for week axis labels. UTC. */
export const fmtWeek = (d: Date | string) => {
  const date = new Date(d);
  return `${date.getUTCDate()}/${date.getUTCMonth() + 1}`;
};

/** A 0–1 ratio as a whole percentage: `0.54` → `54%`. */
export const pct = (x: number) => `${Math.round(x * 100)}%`;

/** The API sends `""` for applications without a role. */
export const UNKNOWN_ROLE_LABEL = "Unknown role";
export const roleLabel = (role: string) => role || UNKNOWN_ROLE_LABEL;

/** `mon` → `Mon`. */
export const fmtWeekday = (day: string) => day.charAt(0).toUpperCase() + day.slice(1);
