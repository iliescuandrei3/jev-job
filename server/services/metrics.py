from collections import Counter, defaultdict
from collections.abc import Sequence
from datetime import date, datetime, timedelta
from statistics import median

from server.schemas.application import Application, Status
from server.schemas.dashboard import (
    BestRoleOut,
    BusiestDayOut,
    FastestRejectionOut,
    FunnelStage,
    FunnelStageOut,
    HeatmapDayOut,
    HeatmapOut,
    HourStatOut,
    InsightsOut,
    KpisOut,
    LongestProcessOut,
    RoleStatOut,
    StatusShareOut,
    Weekday,
    WeekCountsOut,
    WeekdayStatOut,
)
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

# --- Overview (GET /dashboard/overview) ---

# A role needs this many applications before it can be the best-converting role
BEST_ROLE_MIN_APPLICATIONS = 4
_OPEN = {Status.Applied, Status.OA, Status.Interview, Status.Undefined}
# Until the planned `offer` status exists, `accepted` means an offer (see known-issues.md)
_OFFER = {Status.Accepted}
_BREAKDOWN_ORDER = [
    Status.Applied,
    Status.OA,
    Status.Interview,
    Status.Accepted,
    Status.Rejected,
    Status.Ghosted,
    Status.Undefined,
]


def _rate(part: int, whole: int) -> float:
    return part / whole if whole else 0.0

def _median(values: Sequence[float]) -> float | None:
    return median(values) if values else None

def _days(start: datetime, end: datetime) -> float:
    return (end - start).total_seconds() / 86400

def kpis(apps: Sequence[Application]) -> KpisOut:
    total = len(apps)
    replies = [_days(app.appliedAt, app.firstReplyAt) for app in apps if app.firstReplyAt is not None]
    rejection_days = [app.durationDays for app in apps if app.status == Status.Rejected]
    per_company = Counter(app.companyKey for app in apps)
    offers = sum(app.status in _OFFER for app in apps)
    return KpisOut(
        applications=total,
        open=sum(app.status in _OPEN for app in apps),
        companies=len(per_company),
        repeatCompanies=sum(count > 1 for count in per_company.values()),
        responseRate=_rate(len(replies), total),
        medianReplyDays=_median(replies),
        interviewRate=_rate(sum(app.reachedInterview for app in apps), total),
        offers=offers,
        offerRate=_rate(offers, total),
        ghostRate=_rate(sum(app.status == Status.Ghosted for app in apps), total),
        medianRejectionDays=_median(rejection_days),
    )

def funnel(apps: Sequence[Application]) -> list[FunnelStageOut]:
    """applied → replied → interview → offer, each with its conversion from the stage before."""
    values: list[tuple[FunnelStage, int]] = [
        ("applied", len(apps)),
        ("replied", sum(app.firstReplyAt is not None for app in apps)),
        ("interview", sum(app.reachedInterview for app in apps)),
        ("offer", sum(app.status in _OFFER for app in apps)),
    ]
    return [
        FunnelStageOut(
            stage=stage,
            value=value,
            conversion=None if index == 0 else _rate(value, values[index - 1][1]),
        )
        for index, (stage, value) in enumerate(values)
    ]

def status_breakdown(apps: Sequence[Application]) -> list[StatusShareOut]:
    """Applications per current status, in a fixed order. Statuses with no application are left out."""
    counts = Counter(app.status for app in apps)
    return [
        StatusShareOut(status=status, value=counts[status], share=_rate(counts[status], len(apps)))
        for status in _BREAKDOWN_ORDER
        if counts[status]
    ]

def _best_streak(days: set[date]) -> int:
    best = 0
    for day in days:
        if day - timedelta(days=1) in days:
            continue  # not the start of a run
        length = 1
        while day + timedelta(days=length) in days:
            length += 1
        best = max(best, length)
    return best

def _best_role(apps: Sequence[Application]) -> BestRoleOut | None:
    by_role: dict[str, list[Application]] = defaultdict(list)
    for app in apps:
        if app.role:  # an unknown role isn't a role you can aim for
            by_role[app.role].append(app)
    candidates = [
        (role, _rate(sum(app.reachedInterview for app in group), len(group)), len(group))
        for role, group in by_role.items()
        if len(group) >= BEST_ROLE_MIN_APPLICATIONS
    ]
    if not candidates:
        return None
    # Highest rate; ties go to the role with more applications, then alphabetically
    role, rate, _ = min(candidates, key=lambda c: (-c[1], -c[2], c[0].lower(), c[0]))
    return BestRoleOut(role=role, interviewRate=rate)

def insights(apps: Sequence[Application]) -> InsightsOut:
    """Dates are UTC days of `appliedAt`. Ties go to the earlier application or day."""
    rejected = [app for app in apps if app.status == Status.Rejected]
    fastest = min(rejected, key=lambda app: (app.durationDays, app.appliedAt, app.id), default=None)
    longest = min(apps, key=lambda app: (-app.durationDays, app.appliedAt, app.id), default=None)

    per_day = Counter(app.appliedAt.date() for app in apps)
    busiest = min(per_day.items(), key=lambda item: (-item[1], item[0]), default=None)

    return InsightsOut(
        fastestRejection=FastestRejectionOut(
            applicationId=fastest.id, company=fastest.company, role=fastest.role, days=fastest.durationDays,
        ) if fastest else None,
        longestProcess=LongestProcessOut(
            applicationId=longest.id, company=longest.company, status=longest.status, days=longest.durationDays,
        ) if longest else None,
        bestStreakDays=_best_streak(set(per_day)),
        busiestDay=BusiestDayOut(date=busiest[0], count=busiest[1]) if busiest else None,
        bestRole=_best_role(apps),
    )

# --- Timeline (GET /dashboard/timeline) ---

def _monday(day: date) -> date:
    return day - timedelta(days=day.weekday())

def _first_monday(now: datetime, weeks: int) -> date:
    """The Monday that starts a range of `weeks` weeks ending with the current one (UTC)."""
    return _monday(now.date()) - timedelta(weeks=weeks - 1)

def weekly(apps: Sequence[Application], now: datetime, weeks: int) -> list[WeekCountsOut]:
    """`weeks` Monday-to-Sunday weeks (UTC), the last one being the current week; empty weeks included.
    Each application counts in the week of its `appliedAt`, under its current status."""
    first = _first_monday(now, weeks)
    counts: list[Counter[Status]] = [Counter() for _ in range(weeks)]
    for app in apps:
        index = (app.appliedAt.date() - first).days // 7
        if 0 <= index < weeks:
            counts[index][app.status] += 1
    return [
        WeekCountsOut(
            weekStart=first + timedelta(weeks=index),
            counts={status: week[status] for status in _BREAKDOWN_ORDER if week[status]},
        )
        for index, week in enumerate(counts)
    ]

def heatmap(apps: Sequence[Application], now: datetime, weeks: int) -> HeatmapOut:
    """Applications per UTC day, from the Monday `weeks - 1` weeks back through today."""
    start = _first_monday(now, weeks)
    end = now.date()
    per_day = Counter(app.appliedAt.date() for app in apps)
    days = [
        HeatmapDayOut(date=day, count=per_day[day])
        for day in (start + timedelta(days=offset) for offset in range((end - start).days + 1))
    ]
    return HeatmapOut(start=start, end=end, max=max((day.count for day in days), default=0), days=days)
