from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.mandate import MandateCheckResponse
from app.services.country_profiles import get_country_profile, mandate_response

router = APIRouter(prefix="/mandates", tags=["mandates"])


@router.get(
    "/check",
    response_model=MandateCheckResponse,
    summary="Check mandate requirements for a country and transaction type",
    description="Returns MVP mandate metadata for supported country profiles.",
)
def check_mandate(
    country: str = Query(..., min_length=2, max_length=2),
    transaction_type: str = Query(...),
) -> MandateCheckResponse:
    profile = get_country_profile(country, transaction_type)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "UNSUPPORTED_PROFILE",
                "message": "No MVP mandate profile exists for the requested country and transaction type.",
            },
        )
    return mandate_response(profile)
