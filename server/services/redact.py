import os
import re

from dotenv import load_dotenv


load_dotenv()

def _redact(text: str, pii: str, redacted: str) -> str:
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

    return text    