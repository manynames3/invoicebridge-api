from fastapi import APIRouter

from app.core.config import get_settings
from app.core.regions import accepts_regional_writes, configured_regions
from app.schemas.region import RegionDescriptor, RegionTopologyResponse

router = APIRouter(tags=["regions"])


@router.get(
    "/regions",
    response_model=RegionTopologyResponse,
    summary="Get multi-region deployment topology",
    description=(
        "Returns the runtime region, supported regional deployment set, and the intended "
        "write/failover strategy. This is deployment metadata, not a legal compliance decision."
    ),
)
def region_topology() -> RegionTopologyResponse:
    settings = get_settings()
    active_region = settings.deployment_region
    supported_regions = [
        RegionDescriptor(
            name=region,
            role=settings.region_role if region == active_region else "standby",
            active=region == active_region,
            accepts_writes=region == active_region and accepts_regional_writes(),
            data_residency_region=settings.data_residency_region,
            failover_target=settings.failover_region if region == active_region else None,
        )
        for region in configured_regions()
    ]
    return RegionTopologyResponse(
        service=settings.app_name,
        active_region=active_region,
        region_role=settings.region_role,
        data_residency_region=settings.data_residency_region,
        supported_regions=supported_regions,
        write_strategy="regional-primary-writes",
        tenant_routing_strategy="tenant-home-region-with-promoted-failover",
        database_strategy="regional-postgres-primary-with-managed-replicas",
        failover_strategy="dns-or-load-balancer-failover-to-configured-standby-region",
        customer_requirement_fit=[
            "regional processing identity is exposed in health checks and response headers",
            "tenants can be assigned a home region, data-residency region, and failover region",
            "invoice, submission, and audit records persist the processing region",
            "standby regions reject new invoice mutations until promoted to a writable role",
            "idempotency keys protect retried transform/send requests during failover",
            "audit events retain hashes and region metadata for customer evidence",
        ],
    )
