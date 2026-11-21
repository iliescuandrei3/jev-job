from datetime import datetime, timedelta, timezone

from server.schemas.application import Application, Status
from server.schemas.dashboard import DashboardFilters
from server.services.filters import apply_filters

NOW = datetime(2026, 11, 1, 12, tzinfo=timezone.utc)


def _app(app_id: str, company: str, role: str, status: Status, days_ago: float) -> Application:
    applied_at = NOW - timedelta(days=days_ago)
    return Application(
        id=app_id,
        companyKey=company.lower().replace(" ", ""),
        company=company,
        role=role,
        status=status,
        appliedAt=applied_at,
        lastAt=applied_at,
        reachedInterview=False,
        durationDays=0,
        emails=[],
    )

APPS = [
    _app("a", "Spotify", "Backend Engineer", Status.Interview, 10),
    _app("b", "N26", "Data Engineer", Status.Ghosted, 40),
    _app("c", "Magma Math", "Backend Engineer", Status.Rejected, 30),
]


def _ids(filters: DashboardFilters) -> list[str]:
    return [app.id for app in apply_filters(APPS, filters, NOW)]


def test_no_filters_keeps_everything() -> None:
    assert _ids(DashboardFilters()) == ["a", "b", "c"]

def test_q_matches_company_and_role_case_insensitive() -> None:
    assert _ids(DashboardFilters(q="spot")) == ["a"]
    assert _ids(DashboardFilters(q="BACKEND")) == ["a", "c"]

def test_companies_and_roles() -> None:
    assert _ids(DashboardFilters(companies=["n26", "magmamath"])) == ["b", "c"]
    assert _ids(DashboardFilters(roles=["backend engineer"])) == ["a", "c"]

def test_ghosted_status() -> None:
    assert _ids(DashboardFilters(statuses=[Status.Ghosted])) == ["b"]

def test_range_days_boundary_is_inclusive() -> None:
    assert _ids(DashboardFilters(rangeDays=30)) == ["a", "c"]
    assert _ids(DashboardFilters(rangeDays=29)) == ["a"]

def test_filters_combine() -> None:
    assert _ids(DashboardFilters(roles=["Backend Engineer"], statuses=[Status.Rejected], rangeDays=60)) == ["c"]

# "d" has no role
WITH_UNKNOWN = [*APPS, _app("d", "Klarna", "", Status.Applied, 5)]

def _ids_with_unknown(filters: DashboardFilters) -> list[str]:
    return [app.id for app in apply_filters(WITH_UNKNOWN, filters, NOW)]

def test_unknown_role_alone() -> None:
    assert _ids_with_unknown(DashboardFilters(unknownRole=True)) == ["d"]

def test_unknown_role_is_ored_with_roles() -> None:
    assert _ids_with_unknown(DashboardFilters(roles=["Data Engineer"], unknownRole=True)) == ["b", "d"]

def test_roles_without_unknown_role_leave_out_empty_roles() -> None:
    assert _ids_with_unknown(DashboardFilters(roles=["Backend Engineer"])) == ["a", "c"]
    assert _ids_with_unknown(DashboardFilters()) == ["a", "b", "c", "d"]

def test_unknown_role_combines_with_other_filters() -> None:
    assert _ids_with_unknown(DashboardFilters(unknownRole=True, statuses=[Status.Rejected])) == []
    assert _ids_with_unknown(DashboardFilters(unknownRole=True, companies=["klarna"], rangeDays=10)) == ["d"]
