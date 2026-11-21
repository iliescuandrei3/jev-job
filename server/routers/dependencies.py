from typing import Annotated

from fastapi import Query

from server.schemas.dashboard import DashboardFilters


def get_dashboard_filters(filters: Annotated[DashboardFilters, Query()]) -> DashboardFilters:
    return filters
