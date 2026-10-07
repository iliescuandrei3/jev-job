from beanie import Document, Indexed
from typing import Annotated, Optional

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
    isJob: Annotated[Optional[float], Indexed()] = None

    class Settings:
        name = "emails"