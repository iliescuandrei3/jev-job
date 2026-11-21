from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from server.routers.auth import get_current_user
from server.routers.dependencies import get_dashboard_filters
from server.schemas.dashboard import DashboardFilters, FilterOptionsOut, OverviewOut, PatternsOut, SyncOut, TimelineOut
from server.services import metrics
from server.services.dashboard import get_filter_options, get_sync_stats, load_applications

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

@router.get("/overview", response_model=OverviewOut)
async def get_overview(filters: Annotated[DashboardFilters, Depends(get_dashboard_filters)]) -> OverviewOut:
    apps = (await load_applications(filters, datetime.now(timezone.utc))).applications
    return OverviewOut(
        kpis=metrics.kpis(apps),
        funnel=metrics.funnel(apps),
        statusBreakdown=metrics.status_breakdown(apps),
        insights=metrics.insights(apps),
    )

@router.get("/patterns", response_model=PatternsOut)
async def get_patterns(filters: Annotated[DashboardFilters, Depends(get_dashboard_filters)]) -> PatternsOut:
    apps = (await load_applications(filters, datetime.now(timezone.utc))).applications
    return PatternsOut(roles=metrics.roles(apps), weekdays=metrics.weekdays(apps), hours=metrics.hours(apps))

@router.get("/timeline", response_model=TimelineOut)
async def get_timeline(
    filters: Annotated[DashboardFilters, Depends(get_dashboard_filters)],
    weeks: Annotated[int, Query(ge=4, le=104)] = 26,
) -> TimelineOut:
    now = datetime.now(timezone.utc)
    apps = (await load_applications(filters, now)).applications
    return TimelineOut(weekly=metrics.weekly(apps, now, weeks), heatmap=metrics.heatmap(apps, now, weeks))

@router.get("/sync", response_model=SyncOut)
async def get_sync() -> SyncOut:
    # Unfiltered: counts for the whole mailbox
    return await get_sync_stats(datetime.now(timezone.utc))
