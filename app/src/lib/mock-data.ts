// Mock data shaped exactly like the backend `Email` document.
// Replace `MOCK_EMAILS` with a fetch from your API — everything else derives from it.

export type ApplicationStatus = "Applied" | "Interview" | "Offer" | "Rejected" | "Undefined";

export interface Email {
  emailId: string;
  threadId: string;
  labels: string[];
  snippet: string;
  date: string; // ISO
  internalDate: string;
  subject: string;
  toAddress: string;
  toName: string;
  fromAddress: string;
  fromName: string;
  content: string[];
  isJob: number | null;
  applicationStatus: ApplicationStatus;
  company: string;
  role: string;
}

export const NOW = new Date("2026-10-25T12:00:00Z");
const DAY = 86_400_000;

function rng(seed: number) {
  return () => {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const COMPANIES = [
  "Stripe", "Spotify", "Zalando", "N26", "Delivery Hero", "SAP", "Google", "Datadog", "Figma", "Notion",
  "Revolut", "Klarna", "Celonis", "Personio", "Trade Republic", "HelloFresh", "Contentful", "GetYourGuide",
  "Babbel", "Miro", "Vercel", "Supabase", "Cloudflare", "Shopify", "Booking.com", "Adyen", "Mollie",
  "Wolt", "Bolt", "Raisin", "Taxfix", "Pitch", "Mambu", "Sennder", "Enpal", "1Komma5°", "Grover", "Forto",
];
const ROLES = [
  "Frontend Engineer", "Backend Engineer", "Full-Stack Engineer", "Senior Software Engineer",
  "Platform Engineer", "Data Engineer", "Product Engineer", "Staff Engineer", "DevOps Engineer", "ML Engineer",
];

function pick<T>(r: () => number, arr: T[]) {
  return arr[Math.floor(r() * arr.length)];
}

function makeEmails(): Email[] {
  const r = rng(42);
  const out: Email[] = [];
  let id = 0;
  for (let i = 0; i < 150; i++) {
    const company = pick(r, COMPANIES.slice(0, 10 + Math.floor(r() * (COMPANIES.length - 10))));
    const role = pick(r, ROLES);
    const threadId = `t_${i}`;
    const slug = company.toLowerCase().replace(/[^a-z0-9]/g, "");
    // Skew toward recent activity
    const applied = new Date(NOW.getTime() - Math.pow(r(), 1.4) * 280 * DAY);
    applied.setUTCHours(8 + Math.floor(r() * 14), Math.floor(r() * 60));
    const push = (status: ApplicationStatus, d: Date, subject: string, snippet: string) => {
      if (d > NOW) return;
      out.push({
        emailId: `e_${id++}`,
        threadId,
        labels: ["INBOX", "CATEGORY_UPDATES"],
        snippet,
        date: d.toISOString(),
        internalDate: String(d.getTime()),
        subject,
        toAddress: "me@example.com",
        toName: "Me",
        fromAddress: `careers@${slug}.com`,
        fromName: `${company} Talent`,
        content: [snippet],
        isJob: 0.9 + r() * 0.1,
        applicationStatus: status,
        company,
        role,
      });
    };
    push("Applied", applied, `Thanks for applying to ${company}`, `We received your application for ${role}.`);
    const roll = r();
    const after = (days: number) => {
      const d = new Date(applied.getTime() + days * DAY);
      d.setUTCHours(7 + Math.floor(r() * 12), Math.floor(r() * 60));
      return d;
    };
    if (roll < 0.36) {
      push("Rejected", after(0.1 + r() * 25), `Your application at ${company}`, `Unfortunately we decided to move forward with other candidates.`);
    } else if (roll < 0.64) {
      // ghosted / no reply
    } else if (roll < 0.92) {
      const i1 = 3 + r() * 14;
      push("Interview", after(i1), `Interview invitation – ${role}`, `We'd love to schedule a first call with you.`);
      const i2 = i1 + 5 + r() * 10;
      if (r() < 0.6) push("Interview", after(i2), `Next steps: technical interview`, `Great news — we'd like to invite you to the next round.`);
      const o = r();
      if (o < 0.22) push("Offer", after(i2 + 6 + r() * 10), `Offer – ${role} at ${company}`, `We're thrilled to extend you an offer!`);
      else if (o < 0.75) push("Rejected", after(i2 + 3 + r() * 10), `Update on your ${company} process`, `After careful consideration we won't be proceeding.`);
    } else {
      push("Undefined", after(1 + r() * 5), `A quick question from ${company}`, `Could you share your salary expectations?`);
    }
  }
  return out.sort((a, b) => a.date.localeCompare(b.date));
}

export const MOCK_EMAILS: Email[] = makeEmails();
