from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.compliance import CountryProductionReadinessResponse
from app.services.compliance import country_production_readiness

router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.get(
    "/production-readiness",
    response_model=CountryProductionReadinessResponse,
    summary="Check no-paid-network production readiness for a country profile",
    description=(
        "Returns the explicit production blockers for a country profile. This endpoint prevents sandbox-ready "
        "profiles from being misrepresented as legally production-ready."
    ),
)
def production_readiness(
    country: str = Query(..., min_length=2, max_length=2),
    transaction_type: str = Query(default="B2B"),
) -> CountryProductionReadinessResponse:
    readiness = country_production_readiness(country, transaction_type)
    if readiness is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "COUNTRY_PROFILE_NOT_FOUND", "message": "Country profile is not supported."},
        )
    return readiness
