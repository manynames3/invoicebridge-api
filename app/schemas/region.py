from pydantic import BaseModel


class RegionDescriptor(BaseModel):
    name: str
    role: str
    active: bool
    accepts_writes: bool
    data_residency_region: str
    failover_target: str | None = None


class RegionTopologyResponse(BaseModel):
    service: str
    active_region: str
    region_role: str
    data_residency_region: str
    supported_regions: list[RegionDescriptor]
    write_strategy: str
    tenant_routing_strategy: str
    database_strategy: str
    failover_strategy: str
    customer_requirement_fit: list[str]
