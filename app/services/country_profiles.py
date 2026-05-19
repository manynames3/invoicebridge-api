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
    capabilities: tuple[str, ...]
    production_readiness: str


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
    capabilities=(
        "mandate_check",
        "normalized_invoice_validation",
        "ubl_like_xml_transform",
        "xml_export",
        "mock_peppol_submission",
        "status_tracking",
        "audit_trail",
    ),
    production_readiness=(
        "Sandbox workflow only; production Peppol access point and official conformance testing required."
    ),
)

DE_B2B_EN16931_MVP = CountryProfileDefinition(
    name="DE_B2B_EN16931_MVP",
    country="DE",
    transaction_type="B2B",
    mandated=True,
    effective_date=date(2025, 1, 1),
    required_format="XRECHNUNG_EN16931_UBL_LIKE",
    delivery_network="CUSTOMER_MANAGED_DELIVERY_MOCK",
    pdf_allowed_as_compliant_invoice=False,
    implementation_status="MVP_SANDBOX_NO_NETWORK",
    notes=(
        "Germany B2B structured invoice sandbox profile. This MVP validates and transforms invoice data into "
        "EN 16931/XRechnung-style XML for customer-managed delivery; it does not submit through a government "
        "or Peppol network."
    ),
    requires_buyer_routing_id=False,
    requires_vat_ids=True,
    supported_currencies={"EUR"},
    allowed_vat_rates={"0", "7", "19"},
    capabilities=(
        "mandate_check",
        "normalized_invoice_validation",
        "german_vat_id_checksum",
        "xrechnung_en16931_like_xml_transform",
        "xml_export",
        "customer_managed_delivery_record",
        "status_tracking",
        "audit_trail",
    ),
    production_readiness=(
        "Usable for no-network validation/export demos; official KoSIT/XRechnung validation required for production."
    ),
)

PL_B2B_KSEF_MVP = CountryProfileDefinition(
    name="PL_B2B_KSEF_MVP",
    country="PL",
    transaction_type="B2B",
    mandated=True,
    effective_date=date(2026, 2, 1),
    required_format="KSEF_FA3_XML_LIKE",
    delivery_network="KSEF_GOV_SANDBOX_MOCK",
    pdf_allowed_as_compliant_invoice=False,
    implementation_status="MVP_SANDBOX_DIRECT_GOV_API_READY",
    notes=(
        "Poland KSeF sandbox profile. This MVP validates Polish NIP identifiers and transforms invoice data into "
        "FA(3)-inspired XML-like output with a deterministic KSeF sandbox provider boundary; it does not authenticate "
        "with, submit to, or receive official receipts from production KSeF."
    ),
    requires_buyer_routing_id=False,
    requires_vat_ids=True,
    supported_currencies={"PLN", "EUR"},
    allowed_vat_rates={"0", "5", "8", "23"},
    capabilities=(
        "mandate_check",
        "normalized_invoice_validation",
        "polish_nip_checksum",
        "ksef_fa3_like_xml_transform",
        "xml_export",
        "ksef_sandbox_provider_reference",
        "status_tracking",
        "audit_trail",
    ),
    production_readiness=(
        "Sandbox workflow only; production KSeF credentials, encryption, API contract, and UPO handling required."
    ),
)

RO_B2B_EFACTURA_MVP = CountryProfileDefinition(
    name="RO_B2B_EFACTURA_MVP",
    country="RO",
    transaction_type="B2B",
    mandated=True,
    effective_date=date(2024, 1, 1),
    required_format="RO_CIUS_UBL_2_1_XML_LIKE",
    delivery_network="RO_EFACTURA_GOV_SANDBOX_MOCK",
    pdf_allowed_as_compliant_invoice=False,
    implementation_status="MVP_SANDBOX_DIRECT_GOV_API_READY",
    notes=(
        "Romania RO e-Factura sandbox profile. This MVP validates Romanian VAT identifiers and transforms invoice "
        "data into RO_CIUS/UBL 2.1-inspired XML-like output with a deterministic ANAF sandbox provider boundary; "
        "it does not authenticate with SPV, submit to ANAF, or download official signed responses."
    ),
    requires_buyer_routing_id=False,
    requires_vat_ids=True,
    supported_currencies={"RON", "EUR"},
    allowed_vat_rates={"0", "11", "21"},
    capabilities=(
        "mandate_check",
        "normalized_invoice_validation",
        "romanian_cui_checksum",
        "ro_cius_ubl_like_xml_transform",
        "xml_export",
        "anaf_sandbox_provider_reference",
        "status_tracking",
        "audit_trail",
    ),
    production_readiness=(
        "Sandbox workflow only; ANAF/SPV OAuth, upload status polling, and signed response handling required."
    ),
)

ES_B2B_NON_VERIFACTU_MVP = CountryProfileDefinition(
    name="ES_B2B_NON_VERIFACTU_MVP",
    country="ES",
    transaction_type="B2B",
    mandated=True,
    effective_date=date(2027, 1, 1),
    required_format="NON_VERIFACTU_FISCAL_RECORD_XML_LIKE",
    delivery_network="LOCAL_FISCAL_RECORD_MOCK",
    pdf_allowed_as_compliant_invoice=False,
    implementation_status="MVP_SANDBOX_NO_NETWORK",
    notes=(
        "Spain NON-VERI*FACTU-style fiscal record sandbox profile. This MVP generates local invoice record "
        "integrity evidence and audit metadata; a PDF alone is not treated as sufficient evidence. It does not "
        "submit records to AEAT, certify SIF compliance, or implement the Spanish B2B exchange platform."
    ),
    requires_buyer_routing_id=False,
    requires_vat_ids=True,
    supported_currencies={"EUR"},
    allowed_vat_rates={"0", "4", "10", "21"},
    capabilities=(
        "mandate_check",
        "normalized_invoice_validation",
        "spanish_tax_id_checksum",
        "non_verifactu_fiscal_record_transform",
        "xml_export",
        "record_hash_evidence",
        "status_tracking",
        "audit_trail",
    ),
    production_readiness=(
        "Usable for local fiscal-record evidence demos; official SIF/VERI*FACTU conformance remains required."
    ),
)

COUNTRY_PROFILES: dict[tuple[str, str], CountryProfileDefinition] = {
    (BE_B2B_PEPPOL_MVP.country, BE_B2B_PEPPOL_MVP.transaction_type): BE_B2B_PEPPOL_MVP,
    (DE_B2B_EN16931_MVP.country, DE_B2B_EN16931_MVP.transaction_type): DE_B2B_EN16931_MVP,
    (PL_B2B_KSEF_MVP.country, PL_B2B_KSEF_MVP.transaction_type): PL_B2B_KSEF_MVP,
    (RO_B2B_EFACTURA_MVP.country, RO_B2B_EFACTURA_MVP.transaction_type): RO_B2B_EFACTURA_MVP,
    (ES_B2B_NON_VERIFACTU_MVP.country, ES_B2B_NON_VERIFACTU_MVP.transaction_type): ES_B2B_NON_VERIFACTU_MVP,
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
            capabilities=list(profile.capabilities),
            production_readiness=profile.production_readiness,
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
        capabilities=list(profile.capabilities),
        production_readiness=profile.production_readiness,
    )
