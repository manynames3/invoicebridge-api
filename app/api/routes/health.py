from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import get_settings
from app.core.regions import accepts_regional_writes
from app.db.session import SessionLocal

router = APIRouter(tags=["health"])


@router.get("/health", summary="Health check")
def health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": "invoicebridge-api",
        "region": settings.deployment_region,
        "region_role": settings.region_role,
        "data_residency_region": settings.data_residency_region,
    }


@router.get("/health/ready", summary="Readiness check")
def readiness() -> dict[str, str | bool]:
    settings = get_settings()
    with SessionLocal() as db:
        db.execute(text("select 1"))
    return {
        "status": "ready",
        "service": "invoicebridge-api",
        "region": settings.deployment_region,
        "region_role": settings.region_role,
        "accepts_writes": accepts_regional_writes(),
        "database": "ok",
    }
