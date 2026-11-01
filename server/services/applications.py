import re
import unicodedata
from collections import Counter, defaultdict
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone

from server.schemas.application import Application, ApplicationEmail, GroupingResult, Status
from server.schemas.email import ApplicationStatus, JobEmail
from server.settings import (
    ATS_DOMAINS,
    GHOST_AFTER_DAYS,
    LEGAL_SUFFIXES,
    MAIL_PROVIDER_DOMAINS,
    PROCESS_GAP_DAYS,
)

_TERMINAL = {ApplicationStatus.Rejected, ApplicationStatus.Accepted}
_INTERVIEW = {ApplicationStatus.Interview, ApplicationStatus.Accepted}
# Second-level labels of country domains like co.uk or com.au
_SECOND_LEVEL_LABELS = {"co", "com", "ac", "org", "net", "gov"}
# Values the LLM writes when it can't find a company or role
_PLACEHOLDERS = {"undefined", "unknown", "none", "null", "n/a", "na", "-"}
_PLACEHOLDER_PREFIXES = ("not specified", "not mentioned", "not provided", "not stated")


def _as_utc(value: datetime) -> datetime:
    # Mongo returns naive datetimes that are already UTC
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)

def _tokens(text: str) -> list[str]:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", ascii_text.lower()).split()

def _clean(value: str) -> str:
    value = value.strip()
    if value.lower() in _PLACEHOLDERS or value.lower().startswith(_PLACEHOLDER_PREFIXES):
        return ""
    return value

def _strip_parentheses(text: str) -> str:
    # "Company AB (publ)", "Backend Engineer (m/f/d)"
    return re.sub(r"\(.*?\)", " ", text)

def normalise_company(name: str) -> str:
    # "Company.ai" -> "Dema"
    name = re.sub(r"\.[a-z]{2,4}$", "", _strip_parentheses(_clean(name)).strip(), flags=re.IGNORECASE)
    tokens = _tokens(name)
    # Keep at least one token, so a company literally called "AB" still has a key
    while len(tokens) > 1 and tokens[-1] in LEGAL_SUFFIXES:
        tokens.pop()
    # Joined without separators, so "Company Company" and "CompanyCompany" share a key
    return "".join(tokens)

def _normalise_role(role: str) -> str:
    return " ".join(_tokens(_strip_parentheses(_clean(role))))

def _domain_matches(domain: str, entry: str) -> bool:
    if "." in entry:
        return domain == entry or domain.endswith("." + entry)
    return any(label.startswith(entry) for label in domain.split("."))

def _domain_company(from_address: str) -> str:
    domain = from_address.rpartition("@")[2].strip().lower()
    if not domain or any(_domain_matches(domain, entry) for entry in ATS_DOMAINS + MAIL_PROVIDER_DOMAINS):
        return ""

    labels = domain.split(".")
    if len(labels) < 2:
        return ""
    # careers.company.com -> company, mail.example.co.uk -> example
    if len(labels) >= 3 and labels[-2] in _SECOND_LEVEL_LABELS:
        return labels[-3]
    return labels[-2]

def company_key(email: JobEmail) -> str | None:
    key = normalise_company(email.company) or normalise_company(_domain_company(email.fromAddress))
    return key or None

class _Process:
    def __init__(self, email: JobEmail) -> None:
        self.emails: list[JobEmail] = []
        self.role = ""
        self.status = ApplicationStatus.Undefined
        self.add(email)

    def add(self, email: JobEmail) -> None:
        self.emails.append(email)
        if not self.role:
            self.role = _normalise_role(email.role)
        if email.applicationStatus != ApplicationStatus.Undefined:
            self.status = email.applicationStatus

    @property
    def last_at(self) -> datetime:
        return _as_utc(self.emails[-1].date)

    @property
    def is_open(self) -> bool:
        return self.status not in _TERMINAL

def _pick_process(processes: list[_Process], email: JobEmail) -> _Process | None:
    date = _as_utc(email.date)
    recent = [process for process in processes if date - process.last_at <= timedelta(days=PROCESS_GAP_DAYS)]
    if not recent:
        return None

    role = _normalise_role(email.role)
    latest_open = next((process for process in reversed(recent) if process.is_open), None)

    if email.applicationStatus == ApplicationStatus.Applied:
        # A new application, unless it repeats the open one (same or unknown role)
        if latest_open is None:
            return None
        if not role or not latest_open.role or latest_open.role == role:
            return latest_open
        same_role = next((process for process in reversed(recent) if process.is_open and process.role == role), None)
        return same_role

    if role:
        same_role = next((process for process in reversed(recent) if process.role == role), None)
        if same_role is not None:
            return same_role
    # Empty or unmatched role: the latest open process, or the latest one that just ended
    return latest_open or recent[-1]

def _sorted(emails: Sequence[JobEmail]) -> list[JobEmail]:
    return sorted(emails, key=lambda email: (_as_utc(email.date), email.emailId))

def split_into_processes(emails: Sequence[JobEmail]) -> list[list[JobEmail]]:
    """Split one company's emails into application processes."""
    processes: list[_Process] = []
    for email in _sorted(emails):
        process = _pick_process(processes, email)
        if process is None:
            processes.append(_Process(email))
        else:
            process.add(email)
            # Keep the list ordered by last activity, so "recent" checks stay simple
            processes.remove(process)
            processes.append(process)

    return sorted((process.emails for process in processes), key=lambda group: (_as_utc(group[0].date), group[0].emailId))

def _most_common(values: list[str]) -> str:
    # Ties go to the earliest spelling, since Counter keeps insertion order
    values = [_clean(value) for value in values if _clean(value)]
    if not values:
        return ""
    return Counter(values).most_common(1)[0][0]

def derive(group: Sequence[JobEmail], now: datetime) -> Application:
    emails = _sorted(group)
    statuses = [email.applicationStatus for email in emails]
    key = company_key(emails[0]) or ""

    first_applied = next((index for index, status in enumerate(statuses) if status == ApplicationStatus.Applied), None)
    applied_at = _as_utc(emails[first_applied or 0].date)
    last_at = _as_utc(emails[-1].date)

    known = [status for status in statuses if status != ApplicationStatus.Undefined]
    status = Status(known[-1].value) if known else Status.Undefined
    if status == Status.Applied and _as_utc(now) - last_at > timedelta(days=GHOST_AFTER_DAYS):
        status = Status.Ghosted

    # A reply is any later email with a real status; "undefined" emails don't count
    replies = [
        email for email in emails[(first_applied or 0):]
        if email.applicationStatus not in (ApplicationStatus.Applied, ApplicationStatus.Undefined)
    ]

    return Application(
        id=emails[0].emailId,
        companyKey=key,
        company=_most_common([email.company for email in emails]) or key.title(),
        role=_most_common([email.role for email in emails]),
        status=status,
        appliedAt=applied_at,
        lastAt=last_at,
        firstReplyAt=_as_utc(replies[0].date) if replies else None,
        reachedInterview=any(email_status in _INTERVIEW for email_status in statuses),
        durationDays=(last_at - applied_at).total_seconds() / 86400,
        emails=[
            ApplicationEmail(emailId=email.emailId, date=_as_utc(email.date), applicationStatus=email.applicationStatus)
            for email in emails
        ],
    )

def group_into_applications(emails: Sequence[JobEmail], now: datetime) -> GroupingResult:
    by_company: dict[str, list[JobEmail]] = defaultdict(list)
    unassigned = 0
    for email in emails:
        key = company_key(email)
        if key is None:
            unassigned += 1
        else:
            by_company[key].append(email)

    applications = [
        derive(group, now)
        for company_emails in by_company.values()
        for group in split_into_processes(company_emails)
    ]
    applications.sort(key=lambda application: (application.appliedAt, application.id))
    return GroupingResult(applications=applications, unassigned=unassigned)
