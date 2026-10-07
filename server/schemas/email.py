from pydantic import BaseModel, ConfigDict
from typing import Optional


class ParsedEmail(BaseModel):
    model_config = ConfigDict(extra="forbid")

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
    content: list[str]
    isJob: Optional[float] = None
