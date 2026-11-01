"""Print how the stored job emails group into applications.

Run from the repo root with Mongo up:
    uv run --project server python -m server.scripts.inspect_applications
"""
import asyncio
import sys
from collections import Counter
from datetime import datetime, timezone

from server.db.connection import close_db, init_db
from server.db.emails import get_job_emails
from server.services.applications import group_into_applications


def _day(value: datetime | None) -> str:
    return value.strftime("%Y-%m-%d") if value else "-"

async def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    await init_db()
    try:
        emails = await get_job_emails()
    finally:
        await close_db()

    result = group_into_applications(emails, datetime.now(timezone.utc))

    print(f"{'company':<24} {'key':<20} {'role':<32} {'status':<17} {'applied':<10} {'reply':<10} {'last':<10} {'days':>5} {'emails':>6}")
    for app in sorted(result.applications, key=lambda app: (app.companyKey, app.appliedAt)):
        print(
            f"{app.company[:24]:<24} {app.companyKey[:20]:<20} {app.role[:32]:<32} {app.status.value:<17} "
            f"{_day(app.appliedAt):<10} {_day(app.firstReplyAt):<10} {_day(app.lastAt):<10} "
            f"{app.durationDays:>5.0f} {len(app.emails):>6}"
        )

    statuses = Counter(app.status.value for app in result.applications)
    companies = len({app.companyKey for app in result.applications})
    print()
    print(f"{len(emails)} emails -> {len(result.applications)} applications at {companies} companies, {result.unassigned} unassigned")
    print("statuses: " + ", ".join(f"{status} {count}" for status, count in statuses.most_common()))

if __name__ == "__main__":
    asyncio.run(main())
