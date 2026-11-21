from datetime import datetime, timedelta, timezone

from server.schemas.application import Application, ApplicationEmail, ApplicationSort, Status
from server.schemas.email import ApplicationStatus
from server.services.dashboard import get_application, list_applications, sort_applications

NOW = datetime(2026, 11, 1, 12, tzinfo=timezone.utc)


def _app(app_id: str, applied_days_ago: float, last_days_ago: float, email_count: int = 2) -> Application:
    applied_at = NOW - timedelta(days=applied_days_ago)
    last_at = NOW - timedelta(days=last_days_ago)
    step = (last_at - applied_at) / max(email_count - 1, 1)
    emails = [
        ApplicationEmail(emailId=f"{app_id}-{i}", date=applied_at + step * i, applicationStatus=ApplicationStatus.Applied)
        for i in range(email_count)
    ]
    return Application(
        id=app_id,
        companyKey=f"company{app_id}",
        company=f"Company {app_id}",
        role="Backend Engineer",
        status=Status.Applied,
        appliedAt=applied_at,
        lastAt=last_at,
        reachedInterview=False,
        durationDays=(last_at - applied_at).total_seconds() / 86400,
        emails=emails,
    )

# a: newest and shortest · b: middle · c: oldest, longest, most recent activity
APPS = [
    _app("b", 50, 10),
    _app("a", 10, 8),
    _app("c", 60, 2),
]


def _ids(apps: list[Application]) -> list[str]:
    return [app.id for app in apps]

def test_sort_recent() -> None:
    assert _ids(sort_applications(APPS, ApplicationSort.Recent)) == ["a", "b", "c"]

def test_sort_duration() -> None:
    assert _ids(sort_applications(APPS, ApplicationSort.Duration)) == ["c", "b", "a"]

def test_sort_last_activity() -> None:
    assert _ids(sort_applications(APPS, ApplicationSort.LastActivity)) == ["c", "a", "b"]

def test_sort_ties_go_to_most_recent_applied_then_id() -> None:
    tied = [_app("z", 30, 20), _app("y", 20, 10), _app("x", 20, 10)]
    assert _ids(sort_applications(tied, ApplicationSort.Duration)) == ["x", "y", "z"]

def test_limit_and_offset() -> None:
    result = list_applications(APPS, ApplicationSort.Recent, limit=1, offset=1, now=NOW)
    assert result.total == 3
    assert [item.id for item in result.items] == ["b"]

def test_no_limit_returns_everything_after_offset() -> None:
    result = list_applications(APPS, ApplicationSort.Recent, limit=None, offset=1, now=NOW)
    assert [item.id for item in result.items] == ["b", "c"]

def test_offset_past_the_end() -> None:
    result = list_applications(APPS, ApplicationSort.Recent, limit=5, offset=10, now=NOW)
    assert result.total == 3
    assert result.items == []

def test_range_spans_the_returned_items_only() -> None:
    result = list_applications(APPS, ApplicationSort.Recent, limit=2, offset=0, now=NOW)
    # c (60 days ago) is not on the page, so the range starts at b
    assert result.range.start == NOW - timedelta(days=50)
    assert result.range.end == NOW

def test_range_when_nothing_matches() -> None:
    result = list_applications([], ApplicationSort.Recent, limit=None, offset=0, now=NOW)
    assert result.total == 0
    assert result.range.start == NOW
    assert result.range.end == NOW

def test_summary_has_email_count_and_dates_but_no_emails() -> None:
    item = list_applications([_app("a", 10, 4, email_count=3)], ApplicationSort.Recent, None, 0, NOW).items[0]
    assert item.emailCount == 3
    assert item.emailDates == [NOW - timedelta(days=10), NOW - timedelta(days=7), NOW - timedelta(days=4)]
    assert "emails" not in item.model_dump()

def test_get_application() -> None:
    detail = get_application(APPS, "b")
    assert detail is not None
    assert detail.id == "b"
    assert [email.emailId for email in detail.emails] == ["b-0", "b-1"]
    assert all(email.title and email.description for email in detail.emails)

def test_get_application_missing() -> None:
    assert get_application(APPS, "nope") is None
