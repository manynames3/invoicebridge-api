from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TenantCreateRequest(BaseModel):
    tenant_id: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=160)
    home_region: str = Field(min_length=1, max_length=60)
    data_residency_region: str = Field(default="EU", min_length=1, max_length=60)
    failover_region: str | None = Field(default=None, max_length=60)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TenantResponse(BaseModel):
    tenant_id: str
    name: str
    home_region: str
    data_residency_region: str
    failover_region: str | None = None
    active: bool
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class TenantRegionDecisionResponse(BaseModel):
    tenant_id: str
    current_region: str
    write_region: str
    failover_region: str | None = None
    data_residency_region: str
    current_region_allowed: bool
    accepts_writes: bool
    routing_strategy: str
