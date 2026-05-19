from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import Depends, FastAPI, Request, Response, status
from fastapi.responses import JSONResponse

from app.api.routes import compliance, countries, health, invoices, mandates, regions, tenants, webhooks
from app.core.config import get_settings
from app.core.logging import configure_logging, request_id_context
from app.core.rate_limit import NoopRateLimiter
from app.core.regions import region_headers
from app.core.security import require_api_key
from app.db.models import Base, CountryProfile
from app.db.session import SessionLocal, engine
from app.services.country_profiles import COUNTRY_PROFILES

configure_logging()
settings = get_settings()
rate_limiter = NoopRateLimiter()


def response_context_headers(request_id: str) -> dict[str, str]:
    return {"X-Request-ID": request_id, **region_headers()}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if settings.auto_create_tables:
        Base.metadata.create_all(bind=engine)
        _seed_country_profiles()
    yield


app = FastAPI(
    title="InvoiceBridge API",
    description=(
        "MVP API for validating normalized invoice JSON, transforming it into structured invoice "
        "outputs, simulating Peppol-style, customer-managed, government-platform, or local fiscal-record "
        "routing, tracking status, exporting documents, and storing audit trails. This is not a "
        "production-certified Peppol, KSeF, RO e-Factura, VERI*FACTU, or tax-authority submission service."
    ),
    version="0.1.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "health", "description": "Operational health checks."},
        {"name": "compliance", "description": "Production readiness and official validation guardrails."},
        {"name": "countries", "description": "Supported country and network profiles."},
        {"name": "regions", "description": "Runtime region metadata and multi-region topology."},
        {"name": "tenants", "description": "Tenant home-region and failover routing metadata."},
        {"name": "mandates", "description": "Mandate profile lookup."},
        {"name": "invoices", "description": "Validation, transformation, submission, status, and audit APIs."},
        {"name": "webhooks", "description": "Mock webhook utilities."},
    ],
)


@app.middleware("http")
async def request_context_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    token = request_id_context.set(request_id)
    try:
        content_length = request.headers.get("content-length")
        if content_length and not content_length.isdigit():
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "code": "INVALID_CONTENT_LENGTH",
                    "message": "Content-Length must be a positive integer.",
                },
                headers=response_context_headers(request_id),
            )
        if content_length and int(content_length) > settings.max_payload_bytes:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "code": "PAYLOAD_TOO_LARGE",
                    "message": f"Payload exceeds {settings.max_payload_bytes} bytes.",
                },
                headers=response_context_headers(request_id),
            )
        if request.url.path.startswith("/v1"):
            decision = rate_limiter.allow(request)
            if not decision.allowed:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"code": "RATE_LIMITED", "message": decision.reason or "Rate limit exceeded."},
                    headers=response_context_headers(request_id),
                )
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        for header_name, header_value in region_headers().items():
            response.headers[header_name] = header_value
        return response
    finally:
        request_id_context.reset(token)


def _seed_country_profiles() -> None:
    with SessionLocal() as db:
        for profile in COUNTRY_PROFILES.values():
            existing = db.get(CountryProfile, profile.name)
            if existing is None:
                db.add(
                    CountryProfile(
                        id=profile.name,
                        country=profile.country,
                        transaction_type=profile.transaction_type,
                        required_format=profile.required_format,
                        delivery_network=profile.delivery_network,
                        effective_date=profile.effective_date,
                        mandated=profile.mandated,
                        pdf_allowed_as_compliant_invoice=profile.pdf_allowed_as_compliant_invoice,
                        implementation_status=profile.implementation_status,
                        profile_metadata={
                            "notes": profile.notes,
                            "capabilities": list(profile.capabilities),
                            "production_readiness": profile.production_readiness,
                        },
                    )
                )
        db.commit()


app.include_router(health.router)
app.include_router(compliance.router, prefix="/v1", dependencies=[Depends(require_api_key)])
app.include_router(countries.router, prefix="/v1", dependencies=[Depends(require_api_key)])
app.include_router(regions.router, prefix="/v1", dependencies=[Depends(require_api_key)])
app.include_router(tenants.router, prefix="/v1", dependencies=[Depends(require_api_key)])
app.include_router(mandates.router, prefix="/v1", dependencies=[Depends(require_api_key)])
app.include_router(invoices.router, prefix="/v1", dependencies=[Depends(require_api_key)])
app.include_router(webhooks.router, prefix="/v1", dependencies=[Depends(require_api_key)])
