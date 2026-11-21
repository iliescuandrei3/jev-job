from collections import defaultdict
from collections.abc import Sequence

from server.schemas.application import Application
from server.schemas.dashboard import HourStatOut, RoleStatOut, Weekday, WeekdayStatOut
from server.schemas.email import ApplicationStatus

# --- Patterns (GET /dashboard/patterns) ---

TOP_ROLES = 8
# Indexed by Python's weekday(): Monday is 0
_WEEKDAYS: list[Weekday] = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def roles(apps: Sequence[Application]) -> list[RoleStatOut]:
    """The most common roles, as extracted (not normalised). Applications without a role count as role ""."""
    by_role: dict[str, list[Application]] = defaultdict(list)
    for app in apps:
        by_role[app.role].append(app)
    stats = [
        RoleStatOut(
            role=role,
            count=len(group),
            interviewRate=sum(app.reachedInterview for app in group) / len(group),
        )
        for role, group in by_role.items()
    ]
    # Ties go alphabetically, so the cut-off is stable
    stats.sort(key=lambda stat: (-stat.count, stat.role.lower(), stat.role))
    return stats[:TOP_ROLES]

def weekdays(apps: Sequence[Application]) -> list[WeekdayStatOut]:
    """Mon–Sun in UTC: applications by `appliedAt`, rejections by the date of each rejection email."""
    applied = [0] * 7
    rejections = [0] * 7
    for app in apps:
        applied[app.appliedAt.weekday()] += 1
        for email in app.emails:
            if email.applicationStatus == ApplicationStatus.Rejected:
                rejections[email.date.weekday()] += 1
    return [
        WeekdayStatOut(day=day, applied=applied[index], rejections=rejections[index])
        for index, day in enumerate(_WEEKDAYS)
    ]

def hours(apps: Sequence[Application]) -> list[HourStatOut]:
    """Every hour 0–23 (UTC), with the interview and rejection emails that arrived in it."""
    interview = [0] * 24
    rejected = [0] * 24
    for app in apps:
        for email in app.emails:
            if email.applicationStatus == ApplicationStatus.Interview:
                interview[email.date.hour] += 1
            elif email.applicationStatus == ApplicationStatus.Rejected:
                rejected[email.date.hour] += 1
    return [HourStatOut(hour=hour, interview=interview[hour], rejected=rejected[hour]) for hour in range(24)]
