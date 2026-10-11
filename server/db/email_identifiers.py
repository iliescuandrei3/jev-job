from server.db.models import EmailIdentifier
from server.schemas.email import EmailIdentifierData

async def add_email_identifiers(email_identifiers: list[EmailIdentifierData]) -> None:
    for email in email_identifiers:
        await EmailIdentifier(**email.model_dump()).save()

async def get_all_email_identifiers() -> list[EmailIdentifier]:
    return await EmailIdentifier.find_all().to_list()