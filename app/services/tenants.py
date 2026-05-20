from secrets import token_urlsafe

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.regions import accepts_regional_writes, current_region
from app.core.security import hash_api_key
from app.db.models import Tenant, TenantApiKey
from app.schemas.tenant import TenantCreateRequest, TenantCreateResponse, TenantRegionDecisionResponse, TenantResponse


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

    def create(self, request: TenantCreateRequest) -> TenantCreateResponse:
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

        api_key = generate_tenant_api_key()
        tenant = Tenant(
            id=request.tenant_id,
            name=request.name,
            home_region=request.home_region,
            data_residency_region=request.data_residency_region,
            failover_region=request.failover_region,
            active=True,
            tenant_metadata=request.metadata,
        )
        tenant.api_keys.append(
            TenantApiKey(
                name="Default tenant key",
                key_prefix=api_key[:16],
                key_hash=hash_api_key(api_key),
                active=True,
            )
        )
        self.db.add(tenant)
        self.db.commit()
        self.db.refresh(tenant)
        response = tenant_response(tenant).model_dump()
        return TenantCreateResponse(**response, api_key=api_key, api_key_prefix=api_key[:16])

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


def generate_tenant_api_key() -> str:
    return f"ib_tenant_{token_urlsafe(32)}"
