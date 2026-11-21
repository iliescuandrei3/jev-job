from pydantic import BaseModel, ConfigDict, Field

from server.schemas.application import Status


class DashboardFilters(BaseModel):
    # No extra="forbid": used as a Query() model, it would reject the endpoints' own params (sort, limit, weeks)
    q: str | None = None
    companies: list[str] = []
    roles: list[str] = []
    statuses: list[Status] = []
    rangeDays: int | None = Field(default=None, ge=1)

class CompanyOption(BaseModel):
    key: str
    name: str

    model_config = ConfigDict(extra="forbid")

class FilterOptionsOut(BaseModel):
    companies: list[CompanyOption]
    roles: list[str]
    statuses: list[Status]

    model_config = ConfigDict(extra="forbid")
