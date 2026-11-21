from pydantic import BaseModel, ConfigDict

from server.schemas.application import ApplicationOut, Status


class CompanyOut(BaseModel):
    """A tile of the companies grid (GET /companies)."""
    key: str
    name: str
    applications: int
    statuses: list[Status]  # one per application, newest first

    model_config = ConfigDict(extra="forbid")

class CompanyDetailOut(BaseModel):
    """The company history panel (GET /companies/{companyKey}). Unfiltered."""
    key: str
    name: str
    applicationCount: int
    emailCount: int
    repeat: bool  # more than one application
    applications: list[ApplicationOut]  # newest first; emails inside each oldest first

    model_config = ConfigDict(extra="forbid")
