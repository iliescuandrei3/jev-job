from datetime import date, datetime, timedelta, timezone

import pytest

from server.schemas.application import Application, ApplicationEmail, Status
from server.schemas.email import ApplicationStatus
from server.services.metrics import (
    TOP_ROLES,
    funnel,
    heatmap,
    hours,
    insights,
    kpis,
    roles,
    status_breakdown,
    weekdays,
    weekly,
)

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


# --- overview ---

JAN_29 = datetime(2026, 1, 29, 9, tzinfo=timezone.utc)


def _process(
    app_id: str,
    company_key: str,
    role: str,
    status: Status,
    applied_at: datetime,
    duration_days: float,
    reply_after_days: float | None = None,
    reached_interview: bool = False,
) -> Application:
    return Application(
        id=app_id,
        companyKey=company_key,
        company=company_key.title(),
        role=role,
        status=status,
        appliedAt=applied_at,
        lastAt=applied_at + timedelta(days=duration_days),
        firstReplyAt=applied_at + timedelta(days=reply_after_days) if reply_after_days is not None else None,
        reachedInterview=reached_interview,
        durationDays=duration_days,
        emails=[],
    )

def _day(offset: int) -> datetime:
    return JAN_29 + timedelta(days=offset)

# Applied Jan 29, 30, 31 and Feb 1 (a 4-day streak across the month boundary), then Feb 10, 12 (twice) and 20
OVERVIEW_APPS = [
    _process("a", "spotify", "Backend Engineer", Status.Rejected, _day(0), 10, reply_after_days=10),
    _process("b", "spotify", "Backend Engineer", Status.Interview, _day(1), 20, reply_after_days=5, reached_interview=True),
    _process("c", "n26", "Backend Engineer", Status.Accepted, _day(2), 30, reply_after_days=3, reached_interview=True),
    _process("d", "klarna", "Backend Engineer", Status.Ghosted, _day(3), 0),
    _process("e", "klarna", "Data Engineer", Status.Rejected, _day(3), 2, reply_after_days=2),
    _process("f", "zalando", "Data Engineer", Status.Applied, _day(3), 0),
    _process("g", "zalando", "Data Engineer", Status.OA, _day(12), 4, reply_after_days=4),
    _process("h", "hellofresh", "", Status.Undefined, _day(14), 1),
    _process("i", "delivery", "Data Engineer", Status.Rejected, _day(14), 0.5, reply_after_days=0.5),
    _process("j", "miro", "", Status.Ghosted, _day(22), 0),
]


def test_kpis() -> None:
    result = kpis(OVERVIEW_APPS)
    assert result.applications == 10
    assert result.open == 4  # applied, online_assesment, interview, undefined
    assert result.companies == 7
    assert result.repeatCompanies == 3  # spotify, klarna, zalando
    assert result.responseRate == pytest.approx(0.6)
    assert result.medianReplyDays == pytest.approx(3.5)  # median of 0.5, 2, 3, 4, 5, 10
    assert result.interviewRate == pytest.approx(0.2)
    assert result.offers == 1
    assert result.offerRate == pytest.approx(0.1)
    assert result.ghostRate == pytest.approx(0.2)
    assert result.medianRejectionDays == pytest.approx(2)  # median of 0.5, 2, 10

def test_funnel() -> None:
    result = funnel(OVERVIEW_APPS)
    assert [(s.stage, s.value) for s in result] == [("applied", 10), ("replied", 6), ("interview", 2), ("offer", 1)]
    assert result[0].conversion is None
    assert result[1].conversion == pytest.approx(0.6)
    assert result[2].conversion == pytest.approx(2 / 6)
    assert result[3].conversion == pytest.approx(0.5)

def test_status_breakdown_in_fixed_order() -> None:
    result = status_breakdown(OVERVIEW_APPS)
    assert [(s.status, s.value) for s in result] == [
        (Status.Applied, 1),
        (Status.OA, 1),
        (Status.Interview, 1),
        (Status.Accepted, 1),
        (Status.Rejected, 3),
        (Status.Ghosted, 2),
        (Status.Undefined, 1),
    ]
    assert result[4].share == pytest.approx(0.3)
    assert sum(s.share for s in result) == pytest.approx(1)

def test_status_breakdown_omits_zero_counts() -> None:
    result = status_breakdown([_process("a", "spotify", "", Status.Rejected, JAN_29, 1)])
    assert [(s.status, s.value, s.share) for s in result] == [(Status.Rejected, 1, 1.0)]

def test_insights() -> None:
    result = insights(OVERVIEW_APPS)
    assert result.fastestRejection is not None
    assert (result.fastestRejection.applicationId, result.fastestRejection.company) == ("i", "Delivery")
    assert result.fastestRejection.role == "Data Engineer"
    assert result.fastestRejection.days == 0.5
    assert result.longestProcess is not None
    assert (result.longestProcess.applicationId, result.longestProcess.status) == ("c", Status.Accepted)
    assert result.longestProcess.days == 30
    assert result.bestStreakDays == 4
    assert result.busiestDay is not None
    assert (result.busiestDay.date, result.busiestDay.count) == (date(2026, 2, 1), 3)
    assert result.bestRole is not None
    assert (result.bestRole.role, result.bestRole.interviewRate) == ("Backend Engineer", 0.5)

def test_streak_across_month_boundary() -> None:
    feb_27 = datetime(2026, 2, 27, 23, tzinfo=timezone.utc)
    # Feb 27, Feb 28, Mar 1 (2026 is not a leap year), then a gap
    apps = [_process(str(i), "spotify", "", Status.Applied, feb_27 + timedelta(days=i), 0) for i in range(3)]
    apps.append(_process("x", "spotify", "", Status.Applied, datetime(2026, 3, 5, tzinfo=timezone.utc), 0))
    assert insights(apps).bestStreakDays == 3

def test_streak_and_busiest_day_use_utc_days() -> None:
    # 23:00 and 01:00 the next day are two days; 01:00 and 20:00 on the same day are one
    apps = [
        _process("a", "spotify", "", Status.Applied, datetime(2026, 3, 1, 23, tzinfo=timezone.utc), 0),
        _process("b", "spotify", "", Status.Applied, datetime(2026, 3, 2, 1, tzinfo=timezone.utc), 0),
        _process("c", "spotify", "", Status.Applied, datetime(2026, 3, 2, 20, tzinfo=timezone.utc), 0),
    ]
    result = insights(apps)
    assert result.bestStreakDays == 2
    assert result.busiestDay is not None
    assert (result.busiestDay.date, result.busiestDay.count) == (date(2026, 3, 2), 2)

def test_best_role_needs_four_applications_and_a_role() -> None:
    apps = [_process(f"u{i}", "spotify", "", Status.Interview, JAN_29, 1, reached_interview=True) for i in range(5)]
    apps += [_process(f"b{i}", "n26", "Backend Engineer", Status.Applied, JAN_29, 1) for i in range(3)]
    assert insights(apps).bestRole is None

def test_best_role_tie_goes_to_more_applications() -> None:
    apps = [
        _process(f"b{i}", "n26", "Backend Engineer", Status.Interview, JAN_29, 1, reached_interview=i < 2)
        for i in range(4)
    ]
    apps += [
        _process(f"d{i}", "n26", "Data Engineer", Status.Interview, JAN_29, 1, reached_interview=i < 3)
        for i in range(6)
    ]
    result = insights(apps).bestRole
    assert result is not None
    assert (result.role, result.interviewRate) == ("Data Engineer", 0.5)

def test_overview_empty_input() -> None:
    k = kpis([])
    assert (k.applications, k.open, k.companies, k.repeatCompanies, k.offers) == (0, 0, 0, 0, 0)
    assert (k.responseRate, k.interviewRate, k.offerRate, k.ghostRate) == (0, 0, 0, 0)
    assert k.medianReplyDays is None
    assert k.medianRejectionDays is None
    assert [(s.value, s.conversion) for s in funnel([])] == [(0, None), (0, 0), (0, 0), (0, 0)]
    assert status_breakdown([]) == []
    result = insights([])
    assert result.fastestRejection is None
    assert result.longestProcess is None
    assert result.bestStreakDays == 0
    assert result.busiestDay is None
    assert result.bestRole is None


# --- timeline ---

# A Wednesday afternoon; its week starts on Monday 2026-11-16
TIMELINE_NOW = datetime(2026, 11, 18, 15, tzinfo=timezone.utc)
THIS_MONDAY = date(2026, 11, 16)


def _applied(app_id: str, applied_at: datetime, status: Status = Status.Applied) -> Application:
    return _process(app_id, f"company{app_id}", "Backend Engineer", status, applied_at, 0)

def test_weekly_has_every_week_ending_with_the_current_one() -> None:
    result = weekly([], TIMELINE_NOW, 4)
    assert [w.weekStart for w in result] == [THIS_MONDAY - timedelta(weeks=n) for n in (3, 2, 1, 0)]
    assert all(w.weekStart.weekday() == 0 for w in result)
    assert all(w.counts == {} for w in result)

def test_weekly_week_boundary_sunday_vs_monday() -> None:
    sunday_late = datetime(2026, 11, 15, 23, 59, 59, tzinfo=timezone.utc)
    monday_midnight = datetime(2026, 11, 16, 0, 0, tzinfo=timezone.utc)
    result = weekly([_applied("a", sunday_late), _applied("b", monday_midnight)], TIMELINE_NOW, 4)
    assert result[-2].weekStart == date(2026, 11, 9)
    assert result[-2].counts == {Status.Applied: 1}
    assert result[-1].counts == {Status.Applied: 1}

def test_weekly_counts_by_current_status_and_keeps_empty_weeks() -> None:
    apps = [
        _applied("a", datetime(2026, 10, 27, 9, tzinfo=timezone.utc), Status.Rejected),
        _applied("b", datetime(2026, 10, 29, 9, tzinfo=timezone.utc), Status.Rejected),
        _applied("c", datetime(2026, 11, 1, 9, tzinfo=timezone.utc), Status.Ghosted),
        _applied("d", datetime(2026, 11, 17, 9, tzinfo=timezone.utc), Status.Interview),
    ]
    result = weekly(apps, TIMELINE_NOW, 4)
    assert [w.counts for w in result] == [
        {Status.Rejected: 2, Status.Ghosted: 1},
        {},
        {},
        {Status.Interview: 1},
    ]

def test_weekly_ignores_applications_outside_the_range() -> None:
    too_early = datetime(2026, 10, 25, 23, 59, tzinfo=timezone.utc)  # Sunday before the first week
    future = datetime(2026, 11, 23, 9, tzinfo=timezone.utc)  # next week
    result = weekly([_applied("a", too_early), _applied("b", future)], TIMELINE_NOW, 4)
    assert all(w.counts == {} for w in result)

def test_heatmap_starts_on_a_monday_and_ends_today() -> None:
    result = heatmap([], TIMELINE_NOW, 4)
    assert result.start == THIS_MONDAY - timedelta(weeks=3)
    assert result.start.weekday() == 0
    assert result.end == TIMELINE_NOW.date()
    # Three full weeks, then Monday to Wednesday of this week; no days after today
    assert len(result.days) == 3 * 7 + 3
    assert result.days[0].date == result.start
    assert result.days[-1].date == result.end
    assert result.max == 0

def test_heatmap_counts_per_utc_day_and_max() -> None:
    apps = [
        _applied("a", datetime(2026, 11, 2, 0, 0, tzinfo=timezone.utc)),
        _applied("b", datetime(2026, 11, 2, 23, 59, tzinfo=timezone.utc)),
        _applied("c", datetime(2026, 11, 3, 9, tzinfo=timezone.utc)),
        _applied("d", datetime(2026, 10, 1, 9, tzinfo=timezone.utc)),  # before the range
    ]
    result = heatmap(apps, TIMELINE_NOW, 4)
    counts = {d.date: d.count for d in result.days}
    assert counts[date(2026, 11, 2)] == 2
    assert counts[date(2026, 11, 3)] == 1
    assert sum(counts.values()) == 3
    assert result.max == 2

def test_heatmap_on_a_monday_has_one_day_in_the_last_week() -> None:
    monday = datetime(2026, 11, 16, 8, tzinfo=timezone.utc)
    result = heatmap([], monday, 4)
    assert len(result.days) == 3 * 7 + 1
    assert result.days[-1].date == monday.date()
