from typing import Any

from typesafe_sdk import Noul

from server.apis.jev import decide
from server.schemas.email import ParsedEmail

async def _decide_email_application(email: ParsedEmail) -> Any:
    state = email.model_dump(exclude={"content"})
    questions = {
        "isJob": Noul(
            instructions = "Is this email from a job application or a response from a job application?", 
            criteria = {
                "true": "The subject, snippet, labels, and the sender suggest the email is coming from a company as a response to a job application.",
                "false": "The email is not related to a job application.",
            }
        )
    }

    return await decide(state, questions)

async def decide_emails(emails: list[ParsedEmail]) -> list[ParsedEmail]:
    for email in emails:
        decision = await _decide_email_application(email)
        email.isJob = decision.nouls["isJob"].noul

    return emails