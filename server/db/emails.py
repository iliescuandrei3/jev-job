from collections.abc import Sequence

from server.db.models import Email
from server.schemas.email import ParsedEmail


async def add_emails(emails: Sequence[ParsedEmail]) -> None:
    for email in emails:
        await Email(
            **email.model_dump(exclude={"id", "content"}),
        ).save()
