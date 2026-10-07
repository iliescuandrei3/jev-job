from server.apis.gmail import GmailClient
from server.db.emails import add_emails
from server.schemas.email import ParsedEmail
from server.schemas.websocket import JobState
from server.services.email_decision import decide_emails
from server.services.email_parser import parse_emails
from server.websocket import ConnectionManager

async def _get_emails_ids(gmail_client: GmailClient, ws_manager: ConnectionManager, job_id: str) -> tuple[list[str], str]:
    emails_ids = []
    page_count = 1
    batch, next_page_token = await gmail_client.get_email_ids(500, None)
    latest_email_id = batch[0]["id"]
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
        batch, page_token = await gmail_client.get_email_ids(500, next_page_token)
        emails_ids.extend([item["id"] for item in batch])
        next_page_token = page_token
        page_count += 1

        await ws_manager.broadcast_progress(
            job_id, 
            JobState(
                status="running", 
                task_name="Sync emails", 
                message=f"Fetching email ids (Page {page_count})."
            )
        )

    return emails_ids, latest_email_id

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
            if count == 5:
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
            message=f"Fetching labels ..."
        )
    )

    return await gmail_client.get_labels()

async def _make_decisions(ws_manager: ConnectionManager, job_id: str, emails: list[ParsedEmail]):
    await ws_manager.broadcast_progress(
        job_id, 
        JobState(
            status="running", 
            task_name="Sync emails", 
            message=f"Awaiting email decisions ..."
        )
    )
    emails_with_decisions = await decide_emails(emails)
    
    return emails_with_decisions
    

async def sync_all_emails(ws_manager: ConnectionManager, job_id: str):
    # todo: add exception handler
    gmail_client = await GmailClient.create()

    # Get all ids
    emails_ids, latest_email_id = await _get_emails_ids(gmail_client, ws_manager, job_id)
    # Get all emails
    emails = await _get_emails(gmail_client, ws_manager, job_id, emails_ids)
    # Get email labels
    labels = await _get_labels(gmail_client, ws_manager, job_id)
    # Parse eails
    parsed_emails = parse_emails(emails, labels)
    # Make decisions
    emails_with_decisinos = await _make_decisions(ws_manager, job_id, parsed_emails)
    # Save to db
    await add_emails(emails_with_decisinos)
    


async def sync_latest_emails(ws_manager: ConnectionManager, job_id: str, history_id: str):
    pass