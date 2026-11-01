from datetime import datetime
from enum import Enum

from pydantic import BaseModel

from server.schemas.email import ApplicationStatus


class Status(str, Enum):
    Undefined = "undefined"
    Applied = "applied"
    OA = "online_assesment"
    Interview = "interview"
    Accepted = "accepted"
    Rejected = "rejected"
    Ghosted = "ghosted"

class ApplicationEmail(BaseModel):
    emailId: str
    date: datetime
    applicationStatus: ApplicationStatus

class Application(BaseModel):
    id: str
    companyKey: str
    company: str
    role: str
    status: Status
    appliedAt: datetime
    lastAt: datetime
    firstReplyAt: datetime | None = None
    reachedInterview: bool
    durationDays: float
    emails: list[ApplicationEmail]

class GroupingResult(BaseModel):
    applications: list[Application]
    unassigned: int
