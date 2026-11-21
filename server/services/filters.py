from collections.abc import Sequence
from datetime import datetime, timedelta

from server.schemas.application import Application
from server.schemas.dashboard import DashboardFilters


def _matches_role(role: str, filters: DashboardFilters) -> bool:
    if not role:
        return filters.unknownRole
    return role.lower() in {selected.lower() for selected in filters.roles}

def _matches(app: Application, filters: DashboardFilters, since: datetime | None) -> bool:
    if filters.q:
        q = filters.q.strip().lower()
        if q not in app.company.lower() and q not in app.role.lower():
            return False
    if filters.companies and app.companyKey not in filters.companies:
        return False
    if (filters.roles or filters.unknownRole) and not _matches_role(app.role, filters):
        return False
    if filters.statuses and app.status not in filters.statuses:
        return False
    if since is not None and app.appliedAt < since:
        return False
    return True

def apply_filters(apps: Sequence[Application], filters: DashboardFilters, now: datetime) -> list[Application]:
    """Values within one filter are OR'd, different filters are AND'd."""
    since = now - timedelta(days=filters.rangeDays) if filters.rangeDays else None
    return [app for app in apps if _matches(app, filters, since)]
