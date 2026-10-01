import os.path
import json
import base64
from collections import deque

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.labels"]

def get_credentials():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return creds


def seed_emails():
    creds = get_credentials()

    try:
        # Call the Gmail API
        service = build("gmail", "v1", credentials=creds)
        results = service.users().messages().list(userId="me").execute()
        messages = results.get("messages", [])

        with open("data/ids.json", "w") as f:
            json.dump(messages, f)

        if not messages:
            print("No emails found.")
        else:
            emails = {}
            for message in messages:
                msg = (
                    service.users().messages().get(userId="me", id=message["id"]).execute()
                )
                emails[message["id"]] = msg

            with open("data/emails.json", "w") as f:
                json.dump(emails, f)

    except HttpError as error:
        print(f"An error occurred: {error}")


def seed_labels():
    creds = get_credentials()

    try:
        service = build("gmail", "v1", credentials=creds)
        results = service.users().labels().list(userId="me").execute()
        labels = results.get("labels", [])

        with open("data/labels.json", "w") as f:
            json.dump(labels, f)

    except HttpError as error:
        print(f"An error occurred: {error}")


def get_from_headers(headers: dict, key: str) -> str:
    for header in headers:
        if header["name"] == key:
            return header["value"]
    return ""


def get_content_from_parts(payload: dict, mime_type: str) -> list[str]:
    content = []
    parts = deque()

    payload_parts = payload.get("parts", None)
    if payload_parts is not None:
        parts.append(payload_parts)
    while len(parts) > 0:
        current_parts = parts.popleft()
        for part in current_parts:
            part_mime_type = part.get("mimeType", "")
            part_body_data = part.get("body", {}).get("data", "")
            sub_parts = part.get("parts", None)
            if part_mime_type == mime_type:
                content.append(decode_base64(part_body_data))
            if sub_parts is not None:
                parts.append(sub_parts)

    return content

def decode_base64(value: str) -> str:
    padded_value = value + "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(padded_value).decode("utf-8")

def parse_emails():
    parsed = {}
    with open("data/labels.json", "r") as f:
        labels = {label["id"]: label["name"] for label in json.load(f)}

    with open("data/emails.json", "r") as f:
        emails = json.load(f)
        for key, email in emails.items():
            payload = email.get("payload", {})
            headers = payload.get("headers", {})
            parsed[key] = {
                "labels": [labels.get(label_id, label_id) for label_id in email.get("labelIds", [])],
                "threadId": email["threadId"],
                "snippet": email["snippet"],
                "subject": get_from_headers(headers, "Subject"),
                "to": get_from_headers(headers, "To"),
                "from": get_from_headers(headers, "From"),
                "content": get_content_from_parts(payload, "text/plain")
            }
        with open("data/parsed.json", "w") as g:
            json.dump(parsed, g)

if __name__ == "__main__":
    # seed_emails()
    # seed_labels()
    # parse_emails()
    pass
