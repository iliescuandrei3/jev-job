from datetime import datetime, timedelta, timezone

from server.schemas.application import Status
from server.schemas.email import ApplicationStatus, JobEmail
from server.services.applications import (
    company_key,
    derive,
    group_into_applications,
    normalise_company,
    split_into_processes,
)

NOW = datetime(2026, 11, 1, 12, tzinfo=timezone.utc)


def _email(
    email_id: str,
    days_ago: float,
    status: ApplicationStatus,
    company: str = "Spotify",
    role: str = "Backend Engineer",
    from_address: str = "jobs@spotify.com",
) -> JobEmail:
    return JobEmail(
        emailId=email_id,
        date=NOW - timedelta(days=days_ago),
        applicationStatus=status,
        company=company,
        role=role,
        fromAddress=from_address,
    )


def test_one_process_across_threads() -> None:
    emails = [
        _email("a", 30, ApplicationStatus.Applied),
        _email("b", 20, ApplicationStatus.Interview),
        _email("c", 10, ApplicationStatus.Rejected),
    ]

    result = group_into_applications(emails, NOW)

    assert len(result.applications) == 1
    application = result.applications[0]
    assert application.id == "a"
    assert application.status == Status.Rejected
    assert application.reachedInterview is True
    assert application.firstReplyAt == NOW - timedelta(days=20)
    assert application.durationDays == 20
    assert [email.emailId for email in application.emails] == ["a", "b", "c"]


def test_two_roles_at_same_company() -> None:
    emails = [
        _email("a", 30, ApplicationStatus.Applied, role="Backend Engineer"),
        _email("b", 28, ApplicationStatus.Applied, role="Data Engineer"),
        _email("c", 10, ApplicationStatus.Rejected, role="Backend Engineer"),
    ]

    result = group_into_applications(emails, NOW)

    assert len(result.applications) == 2
    by_role = {application.role: application for application in result.applications}
    assert [email.emailId for email in by_role["Backend Engineer"].emails] == ["a", "c"]
    assert by_role["Backend Engineer"].status == Status.Rejected
    assert [email.emailId for email in by_role["Data Engineer"].emails] == ["b"]


def test_new_application_after_rejection() -> None:
    emails = [
        _email("a", 70, ApplicationStatus.Applied),
        _email("b", 60, ApplicationStatus.Rejected),
        _email("c", 30, ApplicationStatus.Applied),
    ]

    groups = split_into_processes(emails)

    assert [[email.emailId for email in group] for group in groups] == [["a", "b"], ["c"]]


def test_new_application_after_long_silence() -> None:
    emails = [
        _email("a", 300, ApplicationStatus.Applied),
        _email("b", 10, ApplicationStatus.Interview),
    ]

    groups = split_into_processes(emails)

    assert len(groups) == 2


def test_empty_role_joins_open_process() -> None:
    emails = [
        _email("a", 30, ApplicationStatus.Applied, role="Backend Engineer"),
        _email("b", 20, ApplicationStatus.Interview, role=""),
    ]

    result = group_into_applications(emails, NOW)

    assert len(result.applications) == 1
    assert result.applications[0].role == "Backend Engineer"
    assert result.applications[0].status == Status.Interview


def test_empty_role_joins_latest_open_process_not_closed_one() -> None:
    emails = [
        _email("a", 40, ApplicationStatus.Applied, role="Backend Engineer"),
        _email("b", 35, ApplicationStatus.Applied, role="Data Engineer"),
        _email("c", 30, ApplicationStatus.Rejected, role="Data Engineer"),
        _email("d", 20, ApplicationStatus.OA, role=""),
    ]

    groups = split_into_processes(emails)

    assert [[email.emailId for email in group] for group in groups] == [["a", "d"], ["b", "c"]]


def test_company_spellings_share_a_key() -> None:
    assert normalise_company("Spotify AB") == "spotify"
    assert normalise_company("spotify") == "spotify"
    assert normalise_company("Deutsche Bank AG") == "deutschebank"
    assert normalise_company("AB") == "ab"
    assert normalise_company("Magma Math") == normalise_company("MagmaMath")
    assert normalise_company("Klarna Bank AB (publ)") == "klarnabank"
    assert normalise_company("Dema.ai") == "dema"
    assert normalise_company("Sandvik Group") == "sandvik"

    emails = [
        _email("a", 30, ApplicationStatus.Applied, company="Spotify AB"),
        _email("b", 20, ApplicationStatus.Interview, company="spotify"),
        _email("c", 10, ApplicationStatus.Interview, company="Spotify AB"),
    ]
    result = group_into_applications(emails, NOW)

    assert len(result.applications) == 1
    assert result.applications[0].companyKey == "spotify"
    assert result.applications[0].company == "Spotify AB"


def test_sender_domain_fallback() -> None:
    email = _email("a", 1, ApplicationStatus.Applied, company="", from_address="no-reply@careers.n26.com")

    assert company_key(email) == "n26"


def test_ats_domain_without_company_is_unassigned() -> None:
    ats = _email("a", 1, ApplicationStatus.Applied, company="", from_address="no-reply@greenhouse.io")
    workday = _email("b", 1, ApplicationStatus.Applied, company="", from_address="acme@myworkdayjobs.com")
    gmail = _email("c", 1, ApplicationStatus.Applied, company="", from_address="recruiter@gmail.com")

    assert company_key(ats) is None
    assert company_key(workday) is None
    assert company_key(gmail) is None

    result = group_into_applications([ats, workday, gmail], NOW)
    assert result.applications == []
    assert result.unassigned == 3


def test_placeholder_values_count_as_empty() -> None:
    placeholder = _email("a", 1, ApplicationStatus.Applied, company="undefined", from_address="no-reply@lever.co")
    assert company_key(placeholder) is None

    emails = [
        _email("b", 30, ApplicationStatus.Applied, role="Backend Engineer"),
        _email("c", 20, ApplicationStatus.Interview, role="undefined"),
        _email("d", 10, ApplicationStatus.Rejected, role="Not specified in the email body"),
    ]
    result = group_into_applications(emails, NOW)

    assert len(result.applications) == 1
    assert result.applications[0].role == "Backend Engineer"


def test_ghosted_after_threshold() -> None:
    ghosted = derive([_email("a", 22, ApplicationStatus.Applied)], NOW)
    waiting = derive([_email("a", 20, ApplicationStatus.Applied)], NOW)

    assert ghosted.status == Status.Ghosted
    assert waiting.status == Status.Applied


def test_assessment_alone_is_not_an_interview() -> None:
    application = derive([_email("a", 5, ApplicationStatus.OA)], NOW)

    assert application.status == Status.OA
    assert application.reachedInterview is False


def test_only_undefined_emails_is_an_undefined_application() -> None:
    emails = [
        _email("a", 10, ApplicationStatus.Undefined),
        _email("b", 5, ApplicationStatus.Undefined),
    ]

    result = group_into_applications(emails, NOW)

    assert len(result.applications) == 1
    assert result.applications[0].status == Status.Undefined
    assert result.applications[0].firstReplyAt is None


def test_undefined_does_not_hide_earlier_status() -> None:
    application = derive(
        [_email("a", 10, ApplicationStatus.Interview), _email("b", 5, ApplicationStatus.Undefined)],
        NOW,
    )

    assert application.status == Status.Interview


def test_naive_mongo_dates_are_utc() -> None:
    email = JobEmail(
        emailId="a",
        date=datetime(2026, 10, 1, 12),
        applicationStatus=ApplicationStatus.Applied,
        company="Spotify",
    )

    application = derive([email], NOW)

    assert application.appliedAt == datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
    assert application.status == Status.Ghosted
