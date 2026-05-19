from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "InvoiceBridge API"
    app_env: str = "local"
    api_key: str = "local-dev-key"
    database_url: str = "sqlite:///./invoicebridge.db"
    auto_create_tables: bool = True
    log_level: str = "INFO"
    max_payload_bytes: int = Field(default=1_048_576, ge=1)
    mock_rejection_threshold: int = Field(default=10_000, ge=0)
    deployment_region: str = "local-dev"
    region_role: str = "local"
    data_residency_region: str = "local"
    active_regions: str = "local-dev"
    failover_region: str | None = None
    xrechnung_validator_command: str | None = None
    ksef_schema_validator_command: str | None = None
    ksef_api_base_url: str | None = None
    ksef_credentials_configured: bool = False
    ro_efactura_schema_validator_command: str | None = None
    ro_efactura_api_base_url: str | None = None
    ro_efactura_oauth_configured: bool = False
    spanish_sif_validator_command: str | None = None
    spanish_sif_signing_configured: bool = False
    spanish_sif_signing_command: str | None = None
    spanish_sif_event_log_configured: bool = False
    spanish_sif_responsible_declaration_ready: bool = False
    spanish_sif_aeat_test_portal_validated: bool = False
    spanish_verifactu_submission_capable: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
