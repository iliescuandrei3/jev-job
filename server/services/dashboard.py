from collections import Counter, defaultdict
from collections.abc import Callable, Sequence
from datetime import datetime

from server.db.emails import get_job_emails
from server.schemas.application import (
    Application,
    ApplicationEmailOut,
    ApplicationListOut,
    ApplicationOut,
    ApplicationSort,
    ApplicationSummaryOut,
    DateRangeOut,
    GroupingResult,
    Status,
)
from server.schemas.dashboard import CompanyOption, DashboardFilters, FilterOptionsOut
from server.services.applications import group_into_applications
from server.services.email_templates import email_text
from server.services.filters import apply_filters

_STATUS_ORDER = [
    Status.Applied,
    Status.OA,
    Status.Interview,
    Status.Accepted,
    Status.Rejected,
    Status.Ghosted,
    Status.Undefined,
]


async def load_applications(filters: DashboardFilters, now: datetime) -> GroupingResult:
    """Group every job email into applications, then filter. `unassigned` is counted before filtering."""
    result = group_into_applications(await get_job_emails(), now)
    return GroupingResult(applications=apply_filters(result.applications, filters, now), unassigned=result.unassigned)

def get_filter_options(apps: Sequence[Application]) -> FilterOptionsOut:
    names: dict[str, list[str]] = defaultdict(list)
    for app in apps:
        names[app.companyKey].append(app.company)
    # One display name per key: the most common one
    companies = [CompanyOption(key=key, name=Counter(values).most_common(1)[0][0]) for key, values in names.items()]
    companies.sort(key=lambda option: option.name.lower())

    roles = sorted({app.role for app in apps if app.role}, key=str.lower)
    unknown_role = any(not app.role for app in apps)
    return FilterOptionsOut(companies=companies, roles=roles, unknownRole=unknown_role, statuses=_STATUS_ORDER)

def to_application_out(app: Application) -> ApplicationOut:
    emails = []
    for email in app.emails:
        title, description = email_text(email.emailId, email.applicationStatus, app.company, app.role)
        emails.append(ApplicationEmailOut(
            emailId=email.emailId,
            date=email.date,
            applicationStatus=email.applicationStatus,
            title=title,
            description=description,
        ))
    return ApplicationOut(
        id=app.id,
        company=app.company,
        companyKey=app.companyKey,
        role=app.role,
        status=app.status,
        appliedAt=app.appliedAt,
        lastAt=app.lastAt,
        durationDays=app.durationDays,
        emails=emails,
    )

_SORT_KEYS: dict[ApplicationSort, Callable[[Application], datetime | float]] = {
    ApplicationSort.Recent: lambda app: app.appliedAt,
    ApplicationSort.Duration: lambda app: app.durationDays,
    ApplicationSort.LastActivity: lambda app: app.lastAt,
}

def sort_applications(apps: Sequence[Application], sort: ApplicationSort) -> list[Application]:
    """Descending by the sort field; ties go to the most recent appliedAt, then id, so the order is stable."""
    by_id = sorted(apps, key=lambda app: app.id)
    by_applied = sorted(by_id, key=lambda app: app.appliedAt, reverse=True)
    return sorted(by_applied, key=_SORT_KEYS[sort], reverse=True)

def _to_summary(app: Application) -> ApplicationSummaryOut:
    return ApplicationSummaryOut(
        id=app.id,
        company=app.company,
        companyKey=app.companyKey,
        role=app.role,
        status=app.status,
        appliedAt=app.appliedAt,
        lastAt=app.lastAt,
        durationDays=app.durationDays,
        emailCount=len(app.emails),
        emailDates=[email.date for email in app.emails],
    )

def list_applications(
    apps: Sequence[Application],
    sort: ApplicationSort,
    limit: int | None,
    offset: int,
    now: datetime,
) -> ApplicationListOut:
    """Sort, then page. `total` counts before paging; `range` spans the returned items up to `now`."""
    ordered = sort_applications(apps, sort)
    page = ordered[offset:] if limit is None else ordered[offset:offset + limit]
    start = min((app.appliedAt for app in page), default=now)
    return ApplicationListOut(
        total=len(ordered),
        range=DateRangeOut(start=start, end=now),
        items=[_to_summary(app) for app in page],
    )

def get_application(apps: Sequence[Application], application_id: str) -> ApplicationOut | None:
    for app in apps:
        if app.id == application_id:
            return to_application_out(app)
    return None
