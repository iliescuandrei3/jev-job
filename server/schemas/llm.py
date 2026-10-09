from pydantic import BaseModel, Field

from server.schemas.email import ApplicationStatus

class EmailStatus(BaseModel):
    applicationStatus: ApplicationStatus
    company: str = Field(pattern=r"^[A-Z0-9]")  # todo: explore if a different type would work better
    role: str                               # todo: explore if a different type would work better