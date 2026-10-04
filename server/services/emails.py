import base64
import json

from server.apis.gmail import GmailClient
from server.schemas.websocket import JobState
from server.websocket import ConnectionManager

def _get_from_headers(headers: dict, key: str) -> str:
    for header in headers:
        if header["name"] == key:
            return header["value"]
    return ""

def _decode_base64(value: str) -> str:
    padded_value = value + "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(padded_value).decode("utf-8")

async def sync_all_emails(ws_manager: ConnectionManager, job_id: str):
    # todo: add exception handler
    # todo: notify on ws if failed
    gmail_client = await GmailClient.create()

    # Get all ids
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

    # Get all emails
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
            if (count + 1) % 100 == 0:
                await ws_manager.broadcast_progress(
                    job_id, 
                    JobState(
                        status="running", 
                        task_name="Sync emails", 
                        message=f"Fetching emails {count + 1}/{len(emails_ids)}."
                    )
                )
                
            # todo: remove this
            if count == 250:
                break

            result = await gmail_client.get_email(message_id)
            emails.append(result)

    print(f"Emails fetched: {len(emails)}")

    await ws_manager.broadcast_progress(
        job_id, 
        JobState(
            status="completed", 
            task_name="Sync emails", 
            message=f"Fetching emails {len(emails_ids)}/{len(emails_ids)}."
        )
    )


def sync_latest_emails(ws_manager: ConnectionManager, job_id: str, history_id: str):
    pass