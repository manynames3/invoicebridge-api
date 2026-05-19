#!/usr/bin/env bash
set -euo pipefail

PRIMARY_URL="${PRIMARY_URL:-http://localhost:8001}"
STANDBY_URL="${STANDBY_URL:-http://localhost:8002}"
API_KEY="${API_KEY:-local-dev-key}"

check_ready() {
  local name="$1"
  local url="$2"
  curl -fsS "$url/health/ready" >/dev/null
  echo "ready: $name $url"
}

check_regions() {
  local name="$1"
  local url="$2"
  curl -fsS -H "X-API-Key: $API_KEY" "$url/v1/regions" >/dev/null
  echo "regions: $name $url"
}

check_tenant_route() {
  local url="$1"
  local tenant_id="smoke-eu-$(date +%s)"
  curl -fsS -X POST "$url/v1/tenants" \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d "{
      \"tenant_id\":\"$tenant_id\",
      \"name\":\"Smoke EU Tenant\",
      \"home_region\":\"eu-west-1\",
      \"data_residency_region\":\"EU\",
      \"failover_region\":\"eu-central-1\"
    }" >/dev/null
  curl -fsS -H "X-API-Key: $API_KEY" "$url/v1/tenants/$tenant_id/region-decision" >/dev/null
  echo "tenant route: $tenant_id"
}

check_ready "primary" "$PRIMARY_URL"
check_ready "standby" "$STANDBY_URL"
check_regions "primary" "$PRIMARY_URL"
check_regions "standby" "$STANDBY_URL"
check_tenant_route "$PRIMARY_URL"

echo "multi-region smoke checks passed"
