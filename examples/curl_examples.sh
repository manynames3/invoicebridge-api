#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
API_KEY="${API_KEY:-local-dev-key}"

curl -s "${BASE_URL}/health"

curl -s -H "X-API-Key: ${API_KEY}" "${BASE_URL}/v1/countries"

curl -s -H "X-API-Key: ${API_KEY}" \
  "${BASE_URL}/v1/compliance/production-readiness?country=DE&transaction_type=B2B"

curl -s -H "X-API-Key: ${API_KEY}" \
  "${BASE_URL}/v1/compliance/production-readiness?country=PL&transaction_type=B2B"

curl -s -H "X-API-Key: ${API_KEY}" \
  "${BASE_URL}/v1/mandates/check?country=BE&transaction_type=B2B"

curl -s -H "X-API-Key: ${API_KEY}" \
  "${BASE_URL}/v1/mandates/check?country=DE&transaction_type=B2B"

curl -s -H "X-API-Key: ${API_KEY}" \
  "${BASE_URL}/v1/mandates/check?country=PL&transaction_type=B2B"

curl -s -H "X-API-Key: ${API_KEY}" \
  "${BASE_URL}/v1/mandates/check?country=RO&transaction_type=B2B"

curl -s -H "X-API-Key: ${API_KEY}" \
  "${BASE_URL}/v1/mandates/check?country=ES&transaction_type=B2B"

curl -s -X POST "${BASE_URL}/v1/invoices/validate" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  --data @examples/belgium_valid_invoice.json

curl -s -X POST "${BASE_URL}/v1/invoices/validate" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  --data @examples/germany_valid_invoice.json

curl -s -X POST "${BASE_URL}/v1/invoices/validate" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  --data @examples/poland_valid_invoice.json

curl -s -X POST "${BASE_URL}/v1/invoices/validate" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  --data @examples/romania_valid_invoice.json

curl -s -X POST "${BASE_URL}/v1/invoices/validate" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  --data @examples/spain_valid_invoice.json

curl -s -X POST "${BASE_URL}/v1/invoices/transform" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Idempotency-Key: demo-transform-001" \
  -H "Content-Type: application/json" \
  --data @examples/belgium_valid_invoice.json

curl -s -X POST "${BASE_URL}/v1/invoices/transform" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Idempotency-Key: demo-transform-de-001" \
  -H "Content-Type: application/json" \
  --data @examples/germany_valid_invoice.json

curl -s -X POST "${BASE_URL}/v1/invoices/transform" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Idempotency-Key: demo-transform-pl-001" \
  -H "Content-Type: application/json" \
  --data @examples/poland_valid_invoice.json

curl -s -X POST "${BASE_URL}/v1/invoices/transform" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Idempotency-Key: demo-transform-ro-001" \
  -H "Content-Type: application/json" \
  --data @examples/romania_valid_invoice.json

curl -s -X POST "${BASE_URL}/v1/invoices/transform" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Idempotency-Key: demo-transform-es-001" \
  -H "Content-Type: application/json" \
  --data @examples/spain_valid_invoice.json

curl -s -X POST "${BASE_URL}/v1/invoices/send" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Idempotency-Key: demo-send-001" \
  -H "Content-Type: application/json" \
  -d "{\"invoice\": $(cat examples/belgium_valid_invoice.json)}"
