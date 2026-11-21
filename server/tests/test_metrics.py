from datetime import datetime, timedelta, timezone

from server.schemas.application import Application, ApplicationEmail, Status
from server.schemas.email import ApplicationStatus
from server.services.metrics import TOP_ROLES, hours, roles, weekdays

# A Monday
MONDAY = datetime(2026, 11, 2, tzinfo=timezone.utc)


def _app(
    app_id: str,
    role: str = "Backend Engineer",
    applied_at: datetime = MONDAY,
    reached_interview: bool = False,
    emails: list[tuple[datetime, ApplicationStatus]] | None = None,
) -> Application:
    email_list = [
        ApplicationEmail(emailId=f"{app_id}-{i}", date=date, applicationStatus=status)
        for i, (date, status) in enumerate(emails or [(applied_at, ApplicationStatus.Applied)])
    ]
    return Application(
        id=app_id,
        companyKey=f"company{app_id}",
        company=f"Company {app_id}",
        role=role,
        status=Status.Applied,
        appliedAt=applied_at,
        lastAt=email_list[-1].date,
        reachedInterview=reached_interview,
        durationDays=0,
        emails=email_list,
    )


# --- roles ---

def test_roles_count_and_interview_rate() -> None:
    apps = [
        _app("a", "Backend Engineer", reached_interview=True),
        _app("b", "Backend Engineer"),
        _app("c", "Data Engineer"),
    ]
    result = roles(apps)
    assert [(r.role, r.count) for r in result] == [("Backend Engineer", 2), ("Data Engineer", 1)]
    assert result[0].interviewRate == 0.5
    assert result[1].interviewRate == 0

def test_roles_are_not_normalised() -> None:
    result = roles([_app("a", "Backend Engineer"), _app("b", "Software Engineer, Backend")])
    assert {r.role for r in result} == {"Backend Engineer", "Software Engineer, Backend"}

def test_roles_include_applications_without_a_role() -> None:
    result = roles([_app("a", "", reached_interview=True), _app("b", ""), _app("c", "Data Engineer")])
    assert result[0].role == ""
    assert result[0].count == 2
    assert result[0].interviewRate == 0.5

def test_roles_top_cut_off_with_stable_ties() -> None:
    apps = [_app("big-1", "Zeta"), _app("big-2", "Zeta")]
    apps += [_app(f"r{i}", f"Role {i}") for i in range(TOP_ROLES + 2)]
    result = roles(apps)
    assert len(result) == TOP_ROLES
    assert result[0].role == "Zeta"
    # The rest tie at 1, so they go alphabetically
    assert [r.role for r in result[1:]] == [f"Role {i}" for i in range(TOP_ROLES - 1)]

def test_roles_empty() -> None:
    assert roles([]) == []


# --- weekdays ---

def test_weekdays_mapping_starts_on_monday() -> None:
    sunday = MONDAY + timedelta(days=6)
    apps = [
        _app("a", applied_at=MONDAY),
        _app("b", applied_at=sunday),
        _app("c", applied_at=sunday + timedelta(hours=23, minutes=59)),
    ]
    result = weekdays(apps)
    assert [row.day for row in result] == ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    assert [row.applied for row in result] == [1, 0, 0, 0, 0, 0, 2]

def test_weekdays_rejections_by_email_date() -> None:
    wednesday = MONDAY + timedelta(days=2)
    friday = MONDAY + timedelta(days=4)
    apps = [
        _app("a", applied_at=MONDAY, emails=[
            (MONDAY, ApplicationStatus.Applied),
            (wednesday, ApplicationStatus.Interview),
            (friday, ApplicationStatus.Rejected),
        ]),
        _app("b", applied_at=MONDAY, emails=[(MONDAY, ApplicationStatus.Applied), (friday, ApplicationStatus.Rejected)]),
    ]
    by_day = {row.day: row for row in weekdays(apps)}
    assert by_day["mon"].applied == 2
    assert by_day["fri"].rejections == 2
    assert by_day["wed"].rejections == 0

def test_weekdays_empty_has_every_day() -> None:
    result = weekdays([])
    assert len(result) == 7
    assert all(row.applied == 0 and row.rejections == 0 for row in result)


# --- hours ---

def test_hours_has_every_hour_even_when_zero() -> None:
    result = hours([])
    assert [row.hour for row in result] == list(range(24))
    assert all(row.interview == 0 and row.rejected == 0 for row in result)

def test_hours_counts_interview_and_rejected_emails_only() -> None:
    apps = [
        _app("a", emails=[
            (MONDAY.replace(hour=9), ApplicationStatus.Applied),
            (MONDAY.replace(hour=9, minute=59), ApplicationStatus.Interview),
            (MONDAY.replace(hour=23), ApplicationStatus.Rejected),
            (MONDAY.replace(hour=0), ApplicationStatus.Accepted),
        ]),
        _app("b", emails=[(MONDAY.replace(hour=9, minute=30), ApplicationStatus.Rejected)]),
    ]
    result = hours(apps)
    assert len(result) == 24
    assert (result[9].interview, result[9].rejected) == (1, 1)
    assert (result[23].interview, result[23].rejected) == (0, 1)
    assert (result[0].interview, result[0].rejected) == (0, 0)
