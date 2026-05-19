from app.core.config import get_settings

WRITE_ROLES = {"local", "primary", "active"}


def configured_regions() -> list[str]:
    settings = get_settings()
    regions = [region.strip() for region in settings.active_regions.split(",") if region.strip()]
    if settings.deployment_region not in regions:
        regions.insert(0, settings.deployment_region)
    return regions


def current_region() -> str:
    return get_settings().deployment_region


def current_region_role() -> str:
    return get_settings().region_role


def current_data_residency_region() -> str:
    return get_settings().data_residency_region


def accepts_regional_writes() -> bool:
    return current_region_role().lower() in WRITE_ROLES


def region_headers() -> dict[str, str]:
    settings = get_settings()
    headers = {
        "X-Deployment-Region": settings.deployment_region,
        "X-Region-Role": settings.region_role,
        "X-Data-Residency-Region": settings.data_residency_region,
    }
    if settings.failover_region:
        headers["X-Failover-Region"] = settings.failover_region
    return headers
