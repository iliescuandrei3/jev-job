from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends

from server.routers.auth import get_current_user
from server.routers.dependencies import get_dashboard_filters
from server.schemas.dashboard import DashboardFilters, FilterOptionsOut, PatternsOut
from server.services import metrics
from server.services.dashboard import get_filter_options, load_applications

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/filters", response_model=FilterOptionsOut)
async def get_filters() -> FilterOptionsOut:
    # Unfiltered, so every option stays selectable
    result = await load_applications(DashboardFilters(), datetime.now(timezone.utc))
    return get_filter_options(result.applications)

@router.get("/patterns", response_model=PatternsOut)
async def get_patterns(filters: Annotated[DashboardFilters, Depends(get_dashboard_filters)]) -> PatternsOut:
    apps = (await load_applications(filters, datetime.now(timezone.utc))).applications
    return PatternsOut(roles=metrics.roles(apps), weekdays=metrics.weekdays(apps), hours=metrics.hours(apps))
