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


@lru_cache
def get_settings() -> Settings:
    return Settings()
