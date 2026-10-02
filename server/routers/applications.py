from fastapi import APIRouter


router = APIRouter(
    prefix="/applications",
    tags=["Applications"],
)

@router.get("/metrics")
async def get_metrics():
    pass

@router.get("/companies")
async def get_companies():
    pass

@router.get("/timeline")
async def get_timieline():
    pass