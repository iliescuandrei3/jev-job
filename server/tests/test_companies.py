from datetime import datetime, timedelta, timezone

from server.schemas.application import Application, ApplicationEmail, Status
from server.schemas.email import ApplicationStatus
from server.services.dashboard import get_company, get_filter_options
from server.services.metrics import companies, company_names

NOW = datetime(2026, 11, 1, 12, tzinfo=timezone.utc)


def _app(app_id: str, company: str, status: Status, applied_days_ago: float, email_count: int = 1) -> Application:
    applied_at = NOW - timedelta(days=applied_days_ago)
    emails = [
        ApplicationEmail(
            emailId=f"{app_id}-{i}",
            date=applied_at + timedelta(days=i),
            applicationStatus=ApplicationStatus.Applied,
        )
        for i in range(email_count)
    ]
    return Application(
        id=app_id,
        companyKey=company.lower().replace(" ", ""),
        company=company,
        role="Backend Engineer",
        status=status,
        appliedAt=applied_at,
        lastAt=emails[-1].date,
        reachedInterview=False,
        durationDays=email_count - 1,
        emails=emails,
    )

APPS = [
    _app("s-old", "Spotify", Status.Rejected, 90, email_count=2),
    _app("n1", "N26", Status.Ghosted, 40),
    _app("s-new", "Spotify", Status.Interview, 10, email_count=3),
    _app("a1", "Adyen", Status.Applied, 5),
]


def test_companies_sorted_by_application_count_then_name() -> None:
    result = companies(APPS)
    assert [company.key for company in result] == ["spotify", "adyen", "n26"]
    assert [company.applications for company in result] == [2, 1, 1]

def test_companies_statuses_newest_application_first() -> None:
    spotify = companies(APPS)[0]
    assert spotify.name == "Spotify"
    assert spotify.statuses == [Status.Interview, Status.Rejected]

def test_companies_empty() -> None:
    assert companies([]) == []

def test_company_names_most_common_variant() -> None:
    apps = [_app("x1", "Spotify", Status.Applied, 3), _app("x2", "Spotify", Status.Applied, 2)]
    variant = apps[1].model_copy(update={"id": "x3", "company": "SPOTIFY"})
    assert company_names([*apps, variant]) == {"spotify": "Spotify"}

def test_filter_options_use_same_names() -> None:
    options = get_filter_options(APPS)
    names = company_names(APPS)
    assert {option.key: option.name for option in options.companies} == names

def test_get_company() -> None:
    detail = get_company(APPS, "spotify")
    assert detail is not None
    assert detail.name == "Spotify"
    assert detail.applicationCount == 2
    assert detail.emailCount == 5
    assert detail.repeat is True
    assert [app.id for app in detail.applications] == ["s-new", "s-old"]
    # Emails inside an application stay oldest first
    assert [email.emailId for email in detail.applications[0].emails] == ["s-new-0", "s-new-1", "s-new-2"]
    assert all(email.title for app in detail.applications for email in app.emails)

def test_get_company_single_application_is_not_repeat() -> None:
    detail = get_company(APPS, "n26")
    assert detail is not None
    assert detail.repeat is False

def test_get_company_unknown_key() -> None:
    assert get_company(APPS, "nope") is None
