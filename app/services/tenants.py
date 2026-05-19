from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.regions import accepts_regional_writes, current_region
from app.db.models import Tenant
from app.schemas.tenant import TenantCreateRequest, TenantRegionDecisionResponse, TenantResponse


def tenant_response(tenant: Tenant) -> TenantResponse:
    return TenantResponse(
        tenant_id=tenant.id,
        name=tenant.name,
        home_region=tenant.home_region,
        data_residency_region=tenant.data_residency_region,
        failover_region=tenant.failover_region,
        active=tenant.active,
        metadata=tenant.tenant_metadata,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
    )


class TenantService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, request: TenantCreateRequest) -> TenantResponse:
        existing = self.db.get(Tenant, request.tenant_id)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "TENANT_ALREADY_EXISTS",
                    "message": "Tenant already exists.",
                    "tenant_id": request.tenant_id,
                },
            )

        tenant = Tenant(
            id=request.tenant_id,
            name=request.name,
            home_region=request.home_region,
            data_residency_region=request.data_residency_region,
            failover_region=request.failover_region,
            active=True,
            tenant_metadata=request.metadata,
        )
        self.db.add(tenant)
        self.db.commit()
        self.db.refresh(tenant)
        return tenant_response(tenant)

    def get(self, tenant_id: str) -> TenantResponse:
        return tenant_response(self.require_active_tenant(tenant_id))

    def region_decision(self, tenant_id: str) -> TenantRegionDecisionResponse:
        tenant = self.require_active_tenant(tenant_id)
        return tenant_region_decision(tenant)

    def require_active_tenant(self, tenant_id: str) -> Tenant:
        tenant = self.db.get(Tenant, tenant_id)
        if tenant is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "TENANT_NOT_FOUND",
                    "message": "Tenant was not found.",
                    "tenant_id": tenant_id,
                },
            )
        if not tenant.active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "TENANT_INACTIVE",
                    "message": "Tenant is inactive.",
                    "tenant_id": tenant_id,
                },
            )
        return tenant


def tenant_region_decision(tenant: Tenant) -> TenantRegionDecisionResponse:
    region = current_region()
    allowed_regions = {tenant.home_region}
    if tenant.failover_region:
        allowed_regions.add(tenant.failover_region)
    return TenantRegionDecisionResponse(
        tenant_id=tenant.id,
        current_region=region,
        write_region=tenant.home_region,
        failover_region=tenant.failover_region,
        data_residency_region=tenant.data_residency_region,
        current_region_allowed=region in allowed_regions,
        accepts_writes=region in allowed_regions and accepts_regional_writes(),
        routing_strategy="tenant-home-region-with-promoted-failover",
    )
