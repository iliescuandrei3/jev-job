import zlib

from server.schemas.email import ApplicationStatus

# (title, description with role, description without role)
_TEMPLATES: dict[ApplicationStatus, list[tuple[str, str, str]]] = {
    ApplicationStatus.Applied: [
        ("Application received by {company}", "Your application for {role} was submitted.", "Your application was submitted."),
        ("Application sent to {company}", "{company} confirmed your application for {role}.", "{company} confirmed your application."),
        ("{company} got your application", "Your application for {role} is in their pipeline.", "Your application is in their pipeline."),
    ],
    ApplicationStatus.OA: [
        ("Online assessment from {company}", "You were invited to an assessment for {role}.", "You were invited to an assessment."),
        ("Assessment invite from {company}", "{company} sent a test for {role}.", "{company} sent a test."),
    ],
    ApplicationStatus.Interview: [
        ("Interview with {company}", "An interview step for {role} was scheduled.", "An interview step was scheduled."),
        ("{company} wants to talk", "You were invited to interview for {role}.", "You were invited to interview."),
        ("Interview update from {company}", "Next steps in the {role} interview process.", "Next steps in the interview process."),
    ],
    ApplicationStatus.Accepted: [
        ("Offer from {company}", "You received an offer for {role}.", "You received an offer."),
        ("Good news from {company}", "{company} made you an offer for {role}.", "{company} made you an offer."),
    ],
    ApplicationStatus.Rejected: [
        ("Update from {company}", "{company} decided not to move forward with {role}.", "{company} decided not to move forward."),
        ("{company} replied", "Your application for {role} was not successful.", "Your application was not successful."),
        ("Decision from {company}", "{company} went with other candidates for {role}.", "{company} went with other candidates."),
    ],
    ApplicationStatus.Undefined: [
        ("Message from {company}", "A recruiting email related to {role}.", "A recruiting email."),
        ("Email from {company}", "An update about your {role} application.", "An update about your application."),
    ],
}


def email_text(email_id: str, status: ApplicationStatus, company: str, role: str) -> tuple[str, str]:
    """Templated title and description for an email, never its real text."""
    templates = _TEMPLATES[status]
    # crc32 is stable across processes, unlike hash(), so the text doesn't change on refresh
    title, with_role, without_role = templates[zlib.crc32(email_id.encode()) % len(templates)]
    description = with_role if role else without_role
    return title.format(company=company), description.format(company=company, role=role)
