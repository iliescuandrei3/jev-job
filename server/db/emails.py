from collections.abc import Sequence

from server.db.models import Email
from server.schemas.email import JobEmail, ParsedEmail


async def add_emails(emails: Sequence[ParsedEmail]) -> None:
    for email in emails:
        await Email(
            **email.model_dump(exclude={"id"}),
        ).save()

async def get_emails() -> list[Email]:
    return await Email.find_all().to_list()

async def get_job_emails() -> list[JobEmail]:
    # The projection loads only the JobEmail fields
    return await Email.find_all(projection_model=JobEmail).sort(+Email.date).to_list()

async def count_emails() -> int:
    return await Email.find_all().count()
