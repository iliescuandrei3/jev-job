from beanie import Document
from typing import Optional

class Email(Document):
    emailId: str
    threadId: str
    labels: list[str]
    snippet: str
    date: str
    subject: str
    toAddress: str
    toName: str
    fromAddress: str
    fromName: str
    # content: str
    isJob: Optional[float] = None

    class Settings:
        name = "emails"