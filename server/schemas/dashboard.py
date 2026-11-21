from datetime import date
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

# --- Overview (GET /dashboard/overview) ---

class KpisOut(BaseModel):
    applications: int
    open: int  # applied, online_assesment, interview or undefined
    companies: int
    repeatCompanies: int  # companies with more than one application
    responseRate: float  # 0–1
    medianReplyDays: float | None  # None without any reply
    interviewRate: float  # 0–1
    offers: int
    offerRate: float  # 0–1
    ghostRate: float  # 0–1
    medianRejectionDays: float | None  # None without any rejection

    model_config = ConfigDict(extra="forbid")

FunnelStage = Literal["applied", "replied", "interview", "offer"]

class FunnelStageOut(BaseModel):
    stage: FunnelStage
    value: int
    conversion: float | None  # 0–1 from the previous stage; None for the first stage

    model_config = ConfigDict(extra="forbid")

class StatusShareOut(BaseModel):
    status: Status
    value: int
    share: float  # 0–1 of all applications

    model_config = ConfigDict(extra="forbid")

class FastestRejectionOut(BaseModel):
    applicationId: str
    company: str
    role: str
    days: float

    model_config = ConfigDict(extra="forbid")

class LongestProcessOut(BaseModel):
    applicationId: str
    company: str
    status: Status
    days: float

    model_config = ConfigDict(extra="forbid")

class BusiestDayOut(BaseModel):
    date: date  # UTC day of appliedAt
    count: int

    model_config = ConfigDict(extra="forbid")

class BestRoleOut(BaseModel):
    role: str
    interviewRate: float  # 0–1

    model_config = ConfigDict(extra="forbid")

class InsightsOut(BaseModel):
    fastestRejection: FastestRejectionOut | None
    longestProcess: LongestProcessOut | None
    bestStreakDays: int  # most consecutive UTC days with at least one application
    busiestDay: BusiestDayOut | None
    bestRole: BestRoleOut | None  # None unless some role has at least BEST_ROLE_MIN_APPLICATIONS

    model_config = ConfigDict(extra="forbid")

class OverviewOut(BaseModel):
    kpis: KpisOut
    funnel: list[FunnelStageOut]
    statusBreakdown: list[StatusShareOut]
    insights: InsightsOut

    model_config = ConfigDict(extra="forbid")
