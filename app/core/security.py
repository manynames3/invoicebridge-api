from dataclasses import dataclass
from hashlib import sha256
from secrets import compare_digest

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.models import TenantApiKey
from app.db.session import get_db

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


@dataclass(frozen=True)
class AuthContext:
    auth_type: str
    tenant_id: str | None = None
    key_prefix: str | None = None

    @property
    def is_admin(self) -> bool:
        return self.auth_type == "admin"


def require_api_key(
    request: Request,
    api_key: str | None = Depends(api_key_header),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
) -> None:
    if not request.url.path.startswith("/v1"):
        return
    auth_context = _auth_context_for_key(api_key, settings, db)
    if auth_context is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "A valid X-API-Key header is required."},
        )
    request.state.auth_context = auth_context


def _valid_api_key(provided: str | None, expected: str) -> bool:
    if not provided:
        return False
    return compare_digest(provided, expected)


def hash_api_key(api_key: str) -> str:
    return sha256(api_key.encode("utf-8")).hexdigest()


def _auth_context_for_key(api_key: str | None, settings: Settings, db: Session) -> AuthContext | None:
    if _valid_api_key(api_key, settings.api_key):
        return AuthContext(auth_type="admin")
    if not api_key:
        return None

    api_key_hash = hash_api_key(api_key)
    tenant_key = db.scalar(
        select(TenantApiKey).where(
            TenantApiKey.key_hash == api_key_hash,
            TenantApiKey.active.is_(True),
        )
    )
    if tenant_key is None or not tenant_key.tenant.active:
        return None

    return AuthContext(
        auth_type="tenant",
        tenant_id=tenant_key.tenant_id,
        key_prefix=tenant_key.key_prefix,
    )


def current_auth_context(request: Request) -> AuthContext:
    context = getattr(request.state, "auth_context", None)
    if isinstance(context, AuthContext):
        return context
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "UNAUTHORIZED", "message": "A valid X-API-Key header is required."},
    )


def require_admin_auth(auth_context: AuthContext = Depends(current_auth_context)) -> AuthContext:
    if auth_context.is_admin:
        return auth_context
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"code": "ADMIN_API_KEY_REQUIRED", "message": "This operation requires the admin API key."},
    )


def require_tenant_or_admin(
    tenant_id: str,
    auth_context: AuthContext = Depends(current_auth_context),
) -> AuthContext:
    if auth_context.is_admin or auth_context.tenant_id == tenant_id:
        return auth_context
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"code": "TENANT_ACCESS_DENIED", "message": "API key is not authorized for this tenant."},
    )
