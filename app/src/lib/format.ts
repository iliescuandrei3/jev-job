// Display formatters. Formatting only: every number comes from the API.

/** Days as `12d`, or hours (`5h`) when under a day. */
export const fmtDays = (d: number) => (d < 1 ? `${Math.max(1, Math.round(d * 24))}h` : `${Math.round(d)}d`);

/** `14 Sept 26`, always in UTC. */
export const fmtDate = (d: Date | string) =>
  new Date(d).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "2-digit", timeZone: "UTC" });

/** A 0–1 ratio as a whole percentage: `0.54` → `54%`. */
export const pct = (x: number) => `${Math.round(x * 100)}%`;
