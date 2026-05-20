from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import AuthContext, require_admin_auth, require_tenant_or_admin
from app.db.session import get_db
from app.schemas.tenant import TenantCreateRequest, TenantCreateResponse, TenantRegionDecisionResponse, TenantResponse
from app.services.tenants import TenantService

router = APIRouter(prefix="/tenants", tags=["tenants"])


def service(db: Session = Depends(get_db)) -> TenantService:
    return TenantService(db)


@router.post(
    "",
    response_model=TenantCreateResponse,
    status_code=201,
    summary="Register a tenant regional routing policy",
    description=(
        "Creates a lightweight tenant record with home, failover, and data-residency regions. "
        "Returns a tenant API key once; store it securely because it is hashed at rest."
    ),
)
def create_tenant(
    request: TenantCreateRequest,
    _: AuthContext = Depends(require_admin_auth),
    tenant_service: TenantService = Depends(service),
) -> TenantCreateResponse:
    return tenant_service.create(request)


@router.get(
    "/{tenant_id}",
    response_model=TenantResponse,
    summary="Get tenant regional routing policy",
)
def get_tenant(
    tenant_id: str,
    _: AuthContext = Depends(require_tenant_or_admin),
    tenant_service: TenantService = Depends(service),
) -> TenantResponse:
    return tenant_service.get(tenant_id)


@router.get(
    "/{tenant_id}/region-decision",
    response_model=TenantRegionDecisionResponse,
    summary="Resolve tenant region decision",
    description="Returns whether the current deployment region is allowed to process writes for the tenant.",
)
def tenant_region_decision(
    tenant_id: str,
    _: AuthContext = Depends(require_tenant_or_admin),
    tenant_service: TenantService = Depends(service),
) -> TenantRegionDecisionResponse:
    return tenant_service.region_decision(tenant_id)
