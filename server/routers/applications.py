from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from server.routers.auth import get_current_user
from server.routers.dependencies import get_dashboard_filters
from server.schemas.application import ApplicationListOut, ApplicationOut, ApplicationSort
from server.schemas.dashboard import DashboardFilters
from server.services.dashboard import get_application, list_applications, load_applications

router = APIRouter(
    prefix="/applications",
    tags=["Applications"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=ApplicationListOut)
async def get_applications(
    filters: Annotated[DashboardFilters, Depends(get_dashboard_filters)],
    sort: ApplicationSort = ApplicationSort.Recent,
    limit: Annotated[int | None, Query(ge=1)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApplicationListOut:
    now = datetime.now(timezone.utc)
    result = await load_applications(filters, now)
    return list_applications(result.applications, sort, limit, offset, now)

@router.get("/{application_id}", response_model=ApplicationOut)
async def get_application_detail(application_id: str) -> ApplicationOut:
    # Unfiltered: a link to one application works whatever the search bar shows
    result = await load_applications(DashboardFilters(), datetime.now(timezone.utc))
    application = get_application(result.applications, application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return application
