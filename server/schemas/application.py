from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict

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

class ApplicationEmailOut(BaseModel):
    emailId: str
    date: datetime
    applicationStatus: ApplicationStatus
    title: str
    description: str

    model_config = ConfigDict(extra="forbid")

class ApplicationOut(BaseModel):
    id: str
    company: str
    companyKey: str
    role: str
    status: Status
    appliedAt: datetime
    lastAt: datetime
    durationDays: float
    emails: list[ApplicationEmailOut]

    model_config = ConfigDict(extra="forbid")
