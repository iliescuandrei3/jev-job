import os
import re

from dotenv import load_dotenv


load_dotenv()

# Any phone-like number: optional "+", then 8+ digits that may be split by spaces, dots, dashes or parentheses.
# Content filters on the LLM APIs block requests containing phone numbers, not only the user's own.
_PHONE_PATTERN = re.compile(r"\+?\(?\d(?:[\s.\-()]*\d){7,}")
# Dates such as 2026-11-21 or 21.11.2026 also match the phone pattern and are kept as they are
_DATE_PATTERN = re.compile(r"\d{4}[-./]\d{1,2}[-./]\d{1,2}|\d{1,2}[-./]\d{1,2}[-./]\d{4}")

def _redact_phone(match: re.Match[str]) -> str:
    return match.group() if _DATE_PATTERN.fullmatch(match.group()) else "[PHONE]"

def _redact(text: str, pii: str | None, redacted: str) -> str:
    if not pii:
        return text
    return re.sub(
        re.escape(pii),
        redacted,
        text,
        flags=re.IGNORECASE,
    )

def redact(text: str) -> str:
    email_address = os.getenv("PERSONAL_EMAIL")
    first = os.getenv("FIRSTNAME")
    last = os.getenv("LASTNAME")
    phone_number = os.getenv("PHONE_NUMBER")

    text = _redact(text, email_address, "[EMAIL_ADDRESS]")
    text = _redact(text, first, "[NAME]")
    text = _redact(text, last, "[NAME]")
    text = _redact(text, phone_number, "[PHONE]")
    text = _PHONE_PATTERN.sub(_redact_phone, text)

    return text    