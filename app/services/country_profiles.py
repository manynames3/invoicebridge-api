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
    implementation_status="COMING_SOON_PRODUCTION_ROADMAP",
    notes=(
        "Belgium B2B Peppol-style evaluation profile. This MVP does not perform official "
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
        "Legal production support coming soon. Production Peppol access point integration and official conformance "
        "testing are required."
    ),
)

DE_B2B_EN16931_MVP = CountryProfileDefinition(
    name="DE_B2B_EN16931_MVP",
    country="DE",
    transaction_type="B2B",
    mandated=True,
    effective_date=date(2025, 1, 1),
    required_format="XRECHNUNG_3_0_UBL",
    delivery_network="CUSTOMER_MANAGED_DELIVERY_MOCK",
    pdf_allowed_as_compliant_invoice=False,
    implementation_status="READY_WITH_OFFICIAL_VALIDATION_REQUIRED",
    notes=(
        "Germany B2B structured invoice profile. This implementation validates German invoice data and transforms "
        "it into XRechnung 3.0 UBL XML for customer-managed delivery. Production reliance requires official "
        "XRechnung/EN16931 validation."
    ),
    requires_buyer_routing_id=False,
    requires_vat_ids=True,
    supported_currencies={"EUR"},
    allowed_vat_rates={"0", "7", "19"},
    capabilities=(
        "mandate_check",
        "normalized_invoice_validation",
        "german_vat_id_checksum",
        "xrechnung_3_0_ubl_transform",
        "xml_export",
        "customer_managed_delivery_record",
        "status_tracking",
        "audit_trail",
    ),
    production_readiness=(
        "No-paid-network production path when generated XML passes official KoSIT/XRechnung validation."
    ),
)

PL_B2B_KSEF_MVP = CountryProfileDefinition(
    name="PL_B2B_KSEF_MVP",
    country="PL",
    transaction_type="B2B",
    mandated=True,
    effective_date=date(2026, 2, 1),
    required_format="KSEF_FA3_XML_LIKE",
    delivery_network="KSEF_GOV_MOCK",
    pdf_allowed_as_compliant_invoice=False,
    implementation_status="COMING_SOON_PRODUCTION_ROADMAP",
    notes=(
        "Poland KSeF evaluation profile. This MVP validates Polish NIP identifiers and transforms invoice data into "
        "FA(3)-inspired XML-like output with a deterministic KSeF mock provider boundary; it does not authenticate "
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
        "ksef_mock_provider_reference",
        "status_tracking",
        "audit_trail",
    ),
    production_readiness=(
        "Legal production support coming soon. Production KSeF credentials, encryption, API contract, and UPO "
        "handling are required."
    ),
)

RO_B2B_EFACTURA_MVP = CountryProfileDefinition(
    name="RO_B2B_EFACTURA_MVP",
    country="RO",
    transaction_type="B2B",
    mandated=True,
    effective_date=date(2024, 1, 1),
    required_format="RO_CIUS_UBL_2_1_XML_LIKE",
    delivery_network="RO_EFACTURA_GOV_MOCK",
    pdf_allowed_as_compliant_invoice=False,
    implementation_status="COMING_SOON_PRODUCTION_ROADMAP",
    notes=(
        "Romania RO e-Factura evaluation profile. This MVP validates Romanian VAT identifiers and transforms invoice "
        "data into RO_CIUS/UBL 2.1-inspired XML-like output with a deterministic ANAF mock provider boundary; "
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
        "anaf_mock_provider_reference",
        "status_tracking",
        "audit_trail",
    ),
    production_readiness=(
        "Legal production support coming soon. ANAF/SPV OAuth, upload status polling, and signed response handling "
        "are required."
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
    implementation_status="COMING_SOON_EXTERNAL_VALIDATION_REQUIRED",
    notes=(
        "Spain NON-VERI*FACTU-style local SIF record profile. This MVP validates Spanish tax IDs, requires "
        "software producer/system identity, VERI*FACTU capability metadata, event-log metadata, and hash-chain "
        "metadata, then generates local invoice record-integrity evidence using AEAT-required hash input fields. "
        "It does not submit records to AEAT, certify SIF compliance, or implement the Spanish B2B exchange platform."
    ),
    requires_buyer_routing_id=False,
    requires_vat_ids=True,
    supported_currencies={"EUR"},
    allowed_vat_rates={"0", "4", "10", "21"},
    capabilities=(
        "mandate_check",
        "normalized_invoice_validation",
        "spanish_tax_id_checksum",
        "non_verifactu_local_sif_record_transform",
        "xml_export",
        "aeat_registro_alta_field_mapping",
        "aeat_xsd_validation_setup",
        "sha256_record_hash_chain",
        "sha256_event_hash_chain",
        "aeat_qr_payload_draft",
        "signing_command_interface",
        "responsible_declaration_metadata",
        "status_tracking",
        "audit_trail",
    ),
    production_readiness=(
        "Legal production support coming soon. Official SIF/VERI*FACTU validation, signing, declaration, and legal "
        "review remain required."
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
