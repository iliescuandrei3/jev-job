import os

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.labels"]

def get_credentials():
    load_dotenv()

    client_id = os.getenv("GMAIL_CLIENT_ID")
    client_secret = os.getenv("GMAIL_CLIENT_SECRET")
    refresh_token = os.getenv("GMAIL_REFRESH_TOKEN")
    if not client_id or not client_secret or not refresh_token:
        raise RuntimeError(
            "Set GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, and GMAIL_REFRESH_TOKEN"
        )

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return creds

def get_email_ids(max_results: int = 500, page_token: str = None) -> tuple[list[dict[str, str]], str | None]:
    service = build("gmail", "v1", credentials=get_credentials())
    results = service.users().messages().list(
        userId="me",
        maxResults=max_results,
        pageToken=page_token,
    ).execute(num_retries = 2)
    messages = results.get("messages", [])
    next_page_token = results.get("nextPageToken", None)
    return messages, next_page_token

def get_emails(message_ids: list[dict[str, str]]) -> tuple[dict[str, dict], dict[str, Exception]]:
    service = build("gmail", "v1", credentials=get_credentials())
    emails = {}
    errors = {}

    def handle_response(request_id, response, exception):
        if exception:
            errors[request_id] = exception
        else:
            emails[request_id] = response

    for start in range(0, len(message_ids), 100):
        batch = service.new_batch_http_request(callback=handle_response)

        for message in message_ids[start : start + 100]:
            message_id = message["id"]
            request = service.users().messages().get(
                userId="me",
                id=message_id,
                format="full",
            )
            batch.add(request, request_id=message_id)

        batch.execute()

    return emails, errors

def get_labels() -> list[dict[str, object]]:
    service = build("gmail", "v1", credentials=get_credentials())
    results = service.users().labels().list(userId="me").execute(num_retries=2)
    return results.get("labels", [])
