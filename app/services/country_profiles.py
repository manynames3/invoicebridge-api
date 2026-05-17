from dataclasses import dataclass
from datetime import date

from app.schemas.mandate import CountryProfileResponse, MandateCheckResponse


@dataclass(frozen=True)
class CountryProfileDefinition:
    name: str
    country: str
    transaction_type: str
    mandated: bool
    effective_date: date | None
    required_format: str
    delivery_network: str
    pdf_allowed_as_compliant_invoice: bool
    implementation_status: str
    notes: str
    requires_buyer_routing_id: bool
    requires_vat_ids: bool
    supported_currencies: set[str]
    allowed_vat_rates: set[str]


BE_B2B_PEPPOL_MVP = CountryProfileDefinition(
    name="BE_B2B_PEPPOL_MVP",
    country="BE",
    transaction_type="B2B",
    mandated=True,
    effective_date=date(2026, 1, 1),
    required_format="PEPPOL_BIS_BILLING_3_UBL_LIKE",
    delivery_network="PEPPOL_MOCK",
    pdf_allowed_as_compliant_invoice=False,
    implementation_status="MVP_SANDBOX",
    notes=(
        "Belgium B2B Peppol-style sandbox profile. This MVP does not perform official "
        "Peppol conformance, access point delivery, or legal certification."
    ),
    requires_buyer_routing_id=True,
    requires_vat_ids=True,
    supported_currencies={"EUR"},
    allowed_vat_rates={"0", "6", "12", "21"},
)

COUNTRY_PROFILES: dict[tuple[str, str], CountryProfileDefinition] = {
    (BE_B2B_PEPPOL_MVP.country, BE_B2B_PEPPOL_MVP.transaction_type): BE_B2B_PEPPOL_MVP,
}


def get_country_profile(country: str | None, transaction_type: str | None) -> CountryProfileDefinition | None:
    if not country or not transaction_type:
        return None
    return COUNTRY_PROFILES.get((country.upper(), transaction_type.upper()))


def list_country_profiles() -> list[CountryProfileResponse]:
    return [
        CountryProfileResponse(
            country=profile.country,
            transaction_types=[profile.transaction_type],
            network=profile.delivery_network,
            required_format=profile.required_format,
            implementation_status=profile.implementation_status,
            profile_name=profile.name,
            notes=profile.notes,
        )
        for profile in COUNTRY_PROFILES.values()
    ]


def mandate_response(profile: CountryProfileDefinition) -> MandateCheckResponse:
    return MandateCheckResponse(
        country=profile.country,
        transaction_type=profile.transaction_type,
        mandated=profile.mandated,
        effective_date=profile.effective_date,
        required_format=profile.required_format,
        delivery_network=profile.delivery_network,
        pdf_allowed_as_compliant_invoice=profile.pdf_allowed_as_compliant_invoice,
        notes=profile.notes,
        implementation_status=profile.implementation_status,
    )
