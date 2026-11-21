from collections import Counter, defaultdict
from collections.abc import Sequence
from datetime import datetime

from server.db.emails import get_job_emails
from server.schemas.application import Application, ApplicationEmailOut, ApplicationOut, GroupingResult, Status
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
    return FilterOptionsOut(companies=companies, roles=roles, statuses=_STATUS_ORDER)

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
