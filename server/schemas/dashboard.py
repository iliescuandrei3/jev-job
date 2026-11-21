from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from server.schemas.application import Status


class DashboardFilters(BaseModel):
    # No extra="forbid": used as a Query() model, it would reject the endpoints' own params (sort, limit, weeks)
    q: str | None = None
    companies: list[str] = []
    roles: list[str] = []
    # Applications without a role; OR'd with `roles`. A flag because "" can't be sent as a query value
    unknownRole: bool = False
    statuses: list[Status] = []
    rangeDays: int | None = Field(default=None, ge=1)

class CompanyOption(BaseModel):
    key: str
    name: str

    model_config = ConfigDict(extra="forbid")

class FilterOptionsOut(BaseModel):
    companies: list[CompanyOption]
    roles: list[str]
    # True when some application has no role (selectable with the `unknownRole` filter)
    unknownRole: bool
    statuses: list[Status]

    model_config = ConfigDict(extra="forbid")

Weekday = Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

class RoleStatOut(BaseModel):
    role: str  # "" for applications without a role
    count: int
    interviewRate: float  # 0–1

    model_config = ConfigDict(extra="forbid")

class WeekdayStatOut(BaseModel):
    day: Weekday
    applied: int
    rejections: int

    model_config = ConfigDict(extra="forbid")

class HourStatOut(BaseModel):
    hour: int  # 0–23, UTC
    interview: int
    rejected: int

    model_config = ConfigDict(extra="forbid")

class PatternsOut(BaseModel):
    roles: list[RoleStatOut]
    weekdays: list[WeekdayStatOut]
    hours: list[HourStatOut]

    model_config = ConfigDict(extra="forbid")
