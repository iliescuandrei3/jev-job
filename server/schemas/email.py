from enum import Enum
from pydantic import BaseModel, ConfigDict
from typing import Optional

class ApplicationStatus(str, Enum):
    Undefined = "undefined"
    Applied = "applied"
    OA = "online_assesment"
    Interview = "interview"
    Accepted = "accepted"
    Rejected = "rejected"
 
class ParsedEmail(BaseModel):
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
    applicationStatus: ApplicationStatus
    company: str # todo: explore if a different type would work better
    role: str # todo: explore if a different type would work better

    model_config = ConfigDict(
        extra="forbid", 
        use_enum_values=True
    )    
