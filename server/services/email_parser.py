import base64
from datetime import datetime, timezone
import re
from collections import deque

from server.schemas.email import ParsedEmail
from server.services.redact import redact


def _decode_base64(value: str) -> str:
    padded_value = value + "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(padded_value).decode("utf-8")

def _get_from_headers(headers: dict, key: str) -> str:
    for header in headers:
        if header["name"] == key:
            return header["value"]
    return ""

def _get_content_from_parts(payload: dict, mime_type: str) -> list[str]:
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
                content.append(_decode_base64(part_body_data))
            if sub_parts is not None:
                parts.append(sub_parts)

    return content

def _parse_email_address(value: str) -> tuple[str, str]:
    email_pattern = r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)+"
    match = re.search(email_pattern, value)
    if match is None:
        return "", value.strip()

    rest = (value[:match.start()] + value[match.end():]).strip().strip('<>"\' ')
    return match.group(), rest

def parse_emails(emails: list[dict], labels: list[dict]) -> list[ParsedEmail]:
    labels_map = {label["id"]: label["name"] for label in labels}

    parsed = []
    for email in emails:
        payload = email.get("payload", {})
        headers = payload.get("headers", {})

        to_address, to_name = _parse_email_address(_get_from_headers(headers, "To"))
        from_address, from_name = _parse_email_address(_get_from_headers(headers, "From"))

        parsed.append(ParsedEmail(**{
            "emailId": email["id"],
            "threadId": email["threadId"],
            "labels": [labels_map.get(label_id, label_id) for label_id in email.get("labelIds", [])],
            "snippet": email["snippet"],
            "date": datetime.fromtimestamp(int(email["internalDate"]) / 1000, tz=timezone.utc),
            "internalDate": email["internalDate"],
            "subject": _get_from_headers(headers, "Subject"),
            "toAddress": to_address,
            "toName": to_name,
            "fromAddress": from_address,
            "fromName": from_name,
            "content": [
                redact(part)
                for part in _get_content_from_parts(payload, "text/plain")
            ]
        }))

    return parsed