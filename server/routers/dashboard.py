from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from server.routers.auth import get_current_user
from server.schemas.dashboard import DashboardFilters, FilterOptionsOut
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
