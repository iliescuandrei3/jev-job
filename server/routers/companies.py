from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from server.routers.auth import get_current_user
from server.routers.dependencies import get_dashboard_filters
from server.schemas.company import CompanyDetailOut, CompanyOut
from server.schemas.dashboard import DashboardFilters
from server.services import metrics
from server.services.dashboard import get_company, load_applications

router = APIRouter(
    prefix="/companies",
    tags=["Companies"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=list[CompanyOut])
async def get_companies(filters: Annotated[DashboardFilters, Depends(get_dashboard_filters)]) -> list[CompanyOut]:
    apps = (await load_applications(filters, datetime.now(timezone.utc))).applications
    return metrics.companies(apps)

@router.get("/{company_key}", response_model=CompanyDetailOut)
async def get_company_detail(company_key: str) -> CompanyDetailOut:
    # Unfiltered: the history panel shows every process with the company, whatever the search bar shows
    result = await load_applications(DashboardFilters(), datetime.now(timezone.utc))
    company = get_company(result.applications, company_key)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return company
