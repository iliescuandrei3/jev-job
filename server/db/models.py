from beanie import Document, Indexed
from typing import Annotated, Optional

from server.schemas.email import ApplicationStatus

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
    applicationStatus: ApplicationStatus
    company: Annotated[str, Indexed()]
    role: Annotated[str, Indexed()]

    class Settings:
        name = "emails"