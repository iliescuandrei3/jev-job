from beanie import Document

class Email(Document):
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

    class Settings:
        name = "emails"