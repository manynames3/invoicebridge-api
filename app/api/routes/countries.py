from fastapi import APIRouter

from app.schemas.mandate import CountryProfileResponse
from app.services.country_profiles import list_country_profiles

router = APIRouter(prefix="/countries", tags=["countries"])


@router.get(
    "",
    response_model=list[CountryProfileResponse],
    summary="List supported e-invoicing country profiles",
    description="Returns jurisdictions, transaction types, networks, and implementation status supported by this MVP.",
)
def countries() -> list[CountryProfileResponse]:
    return list_country_profiles()
