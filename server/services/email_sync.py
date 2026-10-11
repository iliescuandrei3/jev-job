import json

from server.apis.gmail import GmailClient, HistoryType
from server.apis.openrouter import openrouter
from server.db.checkpoint import get_history_checkpoint, update_history_checkpoint
from server.db.emails import add_emails, get_emails
from server.schemas.email import ParsedEmail
from server.schemas.websocket import JobState
from server.services.email_decision import decide_email_application
from server.services.email_parser import parse_emails
from server.services.email_status import get_email_status
from server.websocket import ConnectionManager

_IS_JOB_THRESHOLD = 0.5

async def _get_emails_ids(gmail_client: GmailClient, ws_manager: ConnectionManager, job_id: str) -> tuple[list[str], str]:
    emails_ids = []
    page_count = 1
    batch, next_page_token = await gmail_client.get_email_ids(500, None)
    latest_history_id = batch[0]["historyId"]
    emails_ids.extend([item["id"] for item in batch])
    
    await ws_manager.broadcast_progress(
        job_id, 
        JobState(
            status="running", 
            task_name="Sync emails", 
            message=f"Fetching email ids (Page {page_count})."
        )
    )

    while next_page_token is not None:
        batch, next_page_token = await gmail_client.get_email_ids(500, next_page_token)
        emails_ids.extend([item["id"] for item in batch])
        page_count += 1

        await ws_manager.broadcast_progress(
            job_id, 
            JobState(
                status="running", 
                task_name="Sync emails", 
                message=f"Fetching email ids (Page {page_count})."
            )
        )

    return emails_ids, latest_history_id

async def _get_history_ids(gmail_client: GmailClient, ws_manager: ConnectionManager, job_id: str, start_history_id: str, history_types: list[HistoryType]) -> tuple[list[str], str]:
    emails_ids = []
    page_count = 1
    batch, next_page_token, latest_history_id = await gmail_client.get_history(start_history_id, history_types, 500, None)
    emails_ids.extend([item["message"]["id"] for added in batch for item in added["messagesAdded"] ])
    
    await ws_manager.broadcast_progress(
        job_id, 
        JobState(
            status="running", 
            task_name="Sync latest emails", 
            message=f"Fetching latest email ids (Page {page_count})."
        )
    )

    while next_page_token is not None:
        batch, next_page_token, _ = await gmail_client.get_email_ids(500, next_page_token)
        emails_ids.extend([item["message"]["id"] for added in batch["history"] for item in added["messagesAdded"] ])
        page_count += 1

        await ws_manager.broadcast_progress(
            job_id, 
            JobState(
                status="running", 
                task_name="Sync latest emails", 
                message=f"Fetching latest email ids (Page {page_count})."
            )
        )

    return emails_ids, latest_history_id

async def _get_emails(gmail_client: GmailClient, ws_manager: ConnectionManager, job_id: str, emails_ids: list[str]) -> list[dict]:
    await ws_manager.broadcast_progress(
        job_id, 
        JobState(
            status="running", 
            task_name="Sync emails", 
            message=f"Fetching emails {0}/{len(emails_ids)}."
        )
    )
    emails = []
    for count, message_id in enumerate(emails_ids):
            await ws_manager.broadcast_progress(
                job_id, 
                JobState(
                    status="running", 
                    task_name="Sync emails", 
                    message=f"Fetching emails {count + 1}/{len(emails_ids)}."
                )
            )
                
            # todo: remove this
            if count == 50:
                break

            result = await gmail_client.get_email(message_id)
            emails.append(result)

    return emails

async def _get_labels(gmail_client: GmailClient, ws_manager: ConnectionManager, job_id: str) -> list[dict[str, object]]:
    await ws_manager.broadcast_progress(
        job_id, 
        JobState(
            status="running", 
            task_name="Sync emails", 
            message="Fetching labels ..."
        )
    )

    return await gmail_client.get_labels()

async def _make_decisions(ws_manager: ConnectionManager, job_id: str, emails: list[ParsedEmail]) -> list[ParsedEmail]:
    for count, email in enumerate(emails):
        await ws_manager.broadcast_progress(
            job_id, 
            JobState(
                status="running", 
                task_name="Sync emails", 
                message=f"Awaiting email decisions {count + 1}/{len(emails)}."
            )
        )
        decision = await decide_email_application(email)
        email.isJob = decision.nouls["isJob"].noul
    
    return emails

async def _get_email_status(ws_manager: ConnectionManager, job_id: str, emails: list[ParsedEmail]) -> list[ParsedEmail]:
    async with openrouter() as client:
        for count, email in enumerate(emails):
            await ws_manager.broadcast_progress(
                job_id, 
                JobState(
                    status="running", 
                    task_name="Sync emails", 
                    message=f"Awaiting email statuses {count + 1}/{len(emails)}."
                )
            )
            email_status = await get_email_status(client, email)
            email.applicationStatus = email_status.applicationStatus
            email.company = email_status.company
            email.role = email_status.role

    return emails
        

async def sync_emails(ws_manager: ConnectionManager, job_id: str):
    # todo: add exception handler
    gmail_client = await GmailClient.create()

    start_history_id = await get_history_checkpoint()

    if start_history_id is None: 
    # Get all ids if no start_history_id
        emails_ids, latest_history_id = await _get_emails_ids(gmail_client, ws_manager, job_id)
    else:
    # Get all ids from history
        history_types: list[HistoryType] = ["messageAdded"] 
        emails_ids, latest_history_id = await _get_history_ids(gmail_client, ws_manager, job_id, start_history_id, history_types)
    # Get all emails
    emails = await _get_emails(gmail_client, ws_manager, job_id, emails_ids)
    # Get email labels
    labels = await _get_labels(gmail_client, ws_manager, job_id)
    # Parse eails
    parsed_emails = parse_emails(emails, labels)
    # Make decisions
    emails_with_decisinos = await _make_decisions(ws_manager, job_id, parsed_emails)
    # Filter non-job related emails
    job_emails = [email for email in emails_with_decisinos if email.isJob >= _IS_JOB_THRESHOLD]

    # mock for testing
    # emails = await get_emails()
    # job_emails = [ParsedEmail(**email.model_dump(exclude={"id"})) for email in emails]

    # Get email statueses
    emails_with_status = await _get_email_status(ws_manager, job_id, job_emails)
    
    # Save to db
    await add_emails(emails_with_status)
    # Save the latest history id
    await update_history_checkpoint(latest_history_id)