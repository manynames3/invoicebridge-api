from secrets import compare_digest

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader

from app.core.config import Settings, get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(
    request: Request,
    api_key: str | None = Depends(api_key_header),
    settings: Settings = Depends(get_settings),
) -> None:
    if request.url.path.startswith("/v1") and not _valid_api_key(api_key, settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "A valid X-API-Key header is required."},
        )


def _valid_api_key(provided: str | None, expected: str) -> bool:
    if not provided:
        return False
    return compare_digest(provided, expected)
