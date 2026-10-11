from datetime import datetime, timezone

from server.db.models import FailedEmailIdentifier


async def record_failed_email_id(
    email_id: str,
    status_code: int,
    reason: str,
) -> None:
    failed_identifier = await FailedEmailIdentifier.find_one(
        FailedEmailIdentifier.emailId == email_id
    )
    failed_at = datetime.now(timezone.utc)
    if failed_identifier is None:
        failed_identifier = FailedEmailIdentifier(
            emailId=email_id,
            statusCode=status_code,
            reason=reason,
            lastFailedAt=failed_at,
        )
    else:
        failed_identifier.statusCode = status_code
        failed_identifier.reason = reason
        failed_identifier.lastFailedAt = failed_at

    await failed_identifier.save()
