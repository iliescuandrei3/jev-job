from pydantic import BaseModel, ConfigDict


class ParsedEmail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
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
