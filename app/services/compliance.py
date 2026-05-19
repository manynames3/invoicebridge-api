from app.core.config import Settings, get_settings
from app.schemas.compliance import ComplianceRequirementResponse, CountryProductionReadinessResponse
from app.services.country_profiles import CountryProfileDefinition, get_country_profile


def country_production_readiness(
    country: str | None,
    transaction_type: str | None,
    *,
    settings: Settings | None = None,
) -> CountryProductionReadinessResponse | None:
    profile = get_country_profile(country, transaction_type)
    if profile is None:
        return None

    active_settings = settings or get_settings()
    requirements = _requirements_for_profile(profile, active_settings)
    blockers = [item.message for item in requirements if item.status == "missing"]
    return CountryProductionReadinessResponse(
        country=profile.country,
        transaction_type=profile.transaction_type,
        profile_name=profile.name,
        production_ready=not blockers,
        no_paid_network_path=_no_paid_network_path(profile),
        required_format=profile.required_format,
        delivery_network=profile.delivery_network,
        requirements=requirements,
        blocker_summary=blockers,
    )


def _requirements_for_profile(
    profile: CountryProfileDefinition,
    settings: Settings,
) -> list[ComplianceRequirementResponse]:
    common = [
        _passed(
            "normalized_validation",
            "Normalized invoice validation, tax ID checks, VAT rates, and total consistency are implemented.",
        ),
        _passed("xml_export", "Transformed XML artifact export with SHA-256 hashing is implemented."),
        _passed("audit_trail", "Invoice status and chronological audit trail persistence are implemented."),
    ]

    if profile.country == "DE":
        return [
            *common,
            _configured(
                "official_xrechnung_validation",
                bool(settings.xrechnung_validator_command),
                "Official XRechnung/EN16931 validator command is configured.",
                "Configure XRECHNUNG_VALIDATOR_COMMAND, for example a KoSIT validator invocation.",
            ),
            _passed("customer_managed_delivery", "Germany can use customer-managed delivery without a paid network."),
        ]

    if profile.country == "PL":
        return [
            *common,
            _configured(
                "ksef_schema_validation",
                bool(settings.ksef_schema_validator_command),
                "KSeF FA schema validator command is configured.",
                "Configure KSEF_SCHEMA_VALIDATOR_COMMAND for official FA(3) schema validation.",
            ),
            _configured(
                "ksef_api_endpoint",
                bool(settings.ksef_api_base_url),
                "KSeF API base URL is configured.",
                "Configure KSEF_API_BASE_URL for the official KSeF environment.",
            ),
            _configured(
                "ksef_credentials",
                settings.ksef_credentials_configured,
                "Customer KSeF credentials/certificate configuration is present.",
                "Configure customer-provided KSeF credentials or certificate material outside source control.",
            ),
        ]

    if profile.country == "RO":
        return [
            *common,
            _configured(
                "ro_efactura_schema_validation",
                bool(settings.ro_efactura_schema_validator_command),
                "RO e-Factura/RO_CIUS validator command is configured.",
                "Configure RO_EFACTURA_SCHEMA_VALIDATOR_COMMAND for official XML validation.",
            ),
            _configured(
                "ro_efactura_api_endpoint",
                bool(settings.ro_efactura_api_base_url),
                "ANAF RO e-Factura API base URL is configured.",
                "Configure RO_EFACTURA_API_BASE_URL for the official ANAF environment.",
            ),
            _configured(
                "ro_efactura_oauth",
                settings.ro_efactura_oauth_configured,
                "Customer ANAF/SPV OAuth configuration is present.",
                "Configure customer-provided ANAF/SPV OAuth credentials outside source control.",
            ),
        ]

    if profile.country == "ES":
        return [
            *common,
            _configured(
                "spanish_sif_validation",
                bool(settings.spanish_sif_validator_command),
                "Spanish SIF/VERI*FACTU validator command is configured.",
                "Configure SPANISH_SIF_VALIDATOR_COMMAND for official record validation checks.",
            ),
            _configured(
                "spanish_sif_signing",
                settings.spanish_sif_signing_configured,
                "Spanish SIF record signing configuration is present.",
                "Configure signing material outside source control for fiscal record integrity.",
            ),
            _configured(
                "spanish_responsible_declaration",
                settings.spanish_sif_responsible_declaration_ready,
                "Responsible declaration process is marked ready.",
                "Prepare the customer-specific SIF responsible declaration before production use.",
            ),
        ]

    return [
        *common,
        _configured(
            "official_country_validation",
            False,
            "Official country validator is configured.",
            "No production readiness rule is defined for this profile.",
        ),
    ]


def _no_paid_network_path(profile: CountryProfileDefinition) -> bool:
    return profile.country in {"DE", "ES", "PL", "RO"}


def _passed(code: str, message: str) -> ComplianceRequirementResponse:
    return ComplianceRequirementResponse(code=code, status="passed", message=message)


def _configured(
    code: str,
    condition: bool,
    configured_message: str,
    missing_message: str,
) -> ComplianceRequirementResponse:
    return ComplianceRequirementResponse(
        code=code,
        status="passed" if condition else "missing",
        message=configured_message if condition else missing_message,
        evidence={"configured": condition},
    )
