import os
import re

from dotenv import load_dotenv

load_dotenv()

def redact_email(text: str) -> str:
    email_address = os.getenv("PERSONAL_EMAIL")
    return re.sub(
        re.escape(email_address),
        "[REDACTED_EMAIL]",
        text,
        flags=re.IGNORECASE,
    )