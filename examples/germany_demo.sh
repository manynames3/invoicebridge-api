#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
API_KEY="${API_KEY:-local-dev-key}"
INVOICE_FILE="${INVOICE_FILE:-examples/germany_valid_invoice.json}"
TENANT_ID="${TENANT_ID:-demo-de-$(date +%s)}"

echo "1. Health"
curl -fsS "${BASE_URL}/health"
echo
echo

echo "2. Germany production-readiness blockers"
curl -fsS -H "X-API-Key: ${API_KEY}" \
  "${BASE_URL}/v1/compliance/production-readiness?country=DE&transaction_type=B2B"
echo
echo

echo "3. Create demo tenant and tenant-scoped API key"
TENANT_RESPONSE="$(
  curl -fsS -X POST "${BASE_URL}/v1/tenants" \
    -H "X-API-Key: ${API_KEY}" \
    -H "Content-Type: application/json" \
    -d "{\"tenant_id\":\"${TENANT_ID}\",\"name\":\"Germany Demo Tenant\",\"home_region\":\"local-dev\",\"data_residency_region\":\"EU\",\"failover_region\":\"local-standby\"}"
)"
echo "${TENANT_RESPONSE}"
echo
echo

TENANT_API_KEY="$(
  TENANT_RESPONSE="${TENANT_RESPONSE}" python3 - <<'PY'
import json
import os

print(json.loads(os.environ["TENANT_RESPONSE"])["api_key"])
PY
)"

echo "4. Validate Germany invoice JSON with tenant key"
curl -fsS -X POST "${BASE_URL}/v1/invoices/validate" \
  -H "X-API-Key: ${TENANT_API_KEY}" \
  -H "Content-Type: application/json" \
  --data @"${INVOICE_FILE}"
echo
echo

echo "5. Transform to XRechnung UBL"
TRANSFORM_RESPONSE="$(
  curl -fsS -X POST "${BASE_URL}/v1/invoices/transform" \
    -H "X-API-Key: ${TENANT_API_KEY}" \
    -H "Idempotency-Key: germany-demo-transform-${TENANT_ID}" \
    -H "Content-Type: application/json" \
    --data @"${INVOICE_FILE}"
)"
echo "${TRANSFORM_RESPONSE}"
echo
echo

INVOICE_ID="$(
  TRANSFORM_RESPONSE="${TRANSFORM_RESPONSE}" python3 - <<'PY'
import json
import os

print(json.loads(os.environ["TRANSFORM_RESPONSE"])["invoice_id"])
PY
)"

echo "6. Run configured official validator command"
curl -fsS -X POST "${BASE_URL}/v1/invoices/${INVOICE_ID}/official-validate" \
  -H "X-API-Key: ${TENANT_API_KEY}"
echo
echo

echo "7. Status"
curl -fsS -H "X-API-Key: ${TENANT_API_KEY}" \
  "${BASE_URL}/v1/invoices/status/${INVOICE_ID}"
echo
echo

echo "8. Audit trail"
curl -fsS -H "X-API-Key: ${TENANT_API_KEY}" \
  "${BASE_URL}/v1/invoices/${INVOICE_ID}/audit-trail"
echo
