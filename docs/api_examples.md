# API Examples

Set common variables:

```bash
export BASE_URL=http://localhost:8000
export API_KEY=local-dev-key
```

Health:

```bash
curl -s "$BASE_URL/health"
curl -s "$BASE_URL/health/ready"
```

Countries:

```bash
curl -s -H "X-API-Key: $API_KEY" "$BASE_URL/v1/countries"
```

Region topology:

```bash
curl -s -H "X-API-Key: $API_KEY" "$BASE_URL/v1/regions"
```

Production readiness blockers:

```bash
curl -s -H "X-API-Key: $API_KEY" \
  "$BASE_URL/v1/compliance/production-readiness?country=DE&transaction_type=B2B"

curl -s -H "X-API-Key: $API_KEY" \
  "$BASE_URL/v1/compliance/production-readiness?country=PL&transaction_type=B2B"
```

Register a region-aware tenant:

```bash
curl -s -X POST "$BASE_URL/v1/tenants" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "acme-eu",
    "name": "Acme EU",
    "home_region": "local-dev",
    "data_residency_region": "EU",
    "failover_region": "local-standby"
  }'
```

Resolve tenant routing:

```bash
curl -s -H "X-API-Key: $API_KEY" "$BASE_URL/v1/tenants/acme-eu/region-decision"
```

Mandate check:

```bash
curl -s -H "X-API-Key: $API_KEY" \
  "$BASE_URL/v1/mandates/check?country=BE&transaction_type=B2B"

curl -s -H "X-API-Key: $API_KEY" \
  "$BASE_URL/v1/mandates/check?country=DE&transaction_type=B2B"

curl -s -H "X-API-Key: $API_KEY" \
  "$BASE_URL/v1/mandates/check?country=PL&transaction_type=B2B"

curl -s -H "X-API-Key: $API_KEY" \
  "$BASE_URL/v1/mandates/check?country=RO&transaction_type=B2B"

curl -s -H "X-API-Key: $API_KEY" \
  "$BASE_URL/v1/mandates/check?country=ES&transaction_type=B2B"
```

Validate:

```bash
curl -s -X POST "$BASE_URL/v1/invoices/validate" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  --data @examples/belgium_valid_invoice.json

curl -s -X POST "$BASE_URL/v1/invoices/validate" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  --data @examples/germany_valid_invoice.json

curl -s -X POST "$BASE_URL/v1/invoices/validate" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  --data @examples/poland_valid_invoice.json

curl -s -X POST "$BASE_URL/v1/invoices/validate" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  --data @examples/romania_valid_invoice.json

curl -s -X POST "$BASE_URL/v1/invoices/validate" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  --data @examples/spain_valid_invoice.json
```

Spain validation requires local SIF metadata such as `sif_mode`, `invoice_type`, producer identity, software identity, installation number, `verifactu_capable=true`, `event_log_enabled=true`, `record_timestamp`, and either prior record/event hashes or first-record/first-event flags.

Transform:

```bash
curl -s -X POST "$BASE_URL/v1/invoices/transform" \
  -H "X-API-Key: $API_KEY" \
  -H "Idempotency-Key: transform-demo-001" \
  -H "Content-Type: application/json" \
  --data @examples/belgium_valid_invoice.json

curl -s -X POST "$BASE_URL/v1/invoices/transform" \
  -H "X-API-Key: $API_KEY" \
  -H "Idempotency-Key: transform-demo-de-001" \
  -H "Content-Type: application/json" \
  --data @examples/germany_valid_invoice.json

curl -s -X POST "$BASE_URL/v1/invoices/transform" \
  -H "X-API-Key: $API_KEY" \
  -H "Idempotency-Key: transform-demo-pl-001" \
  -H "Content-Type: application/json" \
  --data @examples/poland_valid_invoice.json

curl -s -X POST "$BASE_URL/v1/invoices/transform" \
  -H "X-API-Key: $API_KEY" \
  -H "Idempotency-Key: transform-demo-ro-001" \
  -H "Content-Type: application/json" \
  --data @examples/romania_valid_invoice.json

curl -s -X POST "$BASE_URL/v1/invoices/transform" \
  -H "X-API-Key: $API_KEY" \
  -H "Idempotency-Key: transform-demo-es-001" \
  -H "Content-Type: application/json" \
  --data @examples/spain_valid_invoice.json
```

Transform responses include `document_url` and `document_sha256` so clients can retrieve and verify the stored artifact.

Download transformed XML:

```bash
curl -s -H "X-API-Key: $API_KEY" \
  "$BASE_URL/v1/invoices/REPLACE_ME/document"
```

Run configured official validator command:

```bash
curl -s -X POST "$BASE_URL/v1/invoices/REPLACE_ME/official-validate" \
  -H "X-API-Key: $API_KEY"
```

For Spain SIF schema checks, install AEAT assets first:

```bash
make setup-spanish-sif-assets
export SPANISH_SIF_VALIDATOR_COMMAND="vendor/spanish-sif/validate-spanish-sif.sh {xml}"
```

Generate Spain responsible-declaration draft evidence:

```bash
curl -s -H "X-API-Key: $API_KEY" \
  "$BASE_URL/v1/invoices/REPLACE_ME/spain/responsible-declaration"
```

Send:

```bash
curl -s -X POST "$BASE_URL/v1/invoices/send" \
  -H "X-API-Key: $API_KEY" \
  -H "Idempotency-Key: send-demo-001" \
  -H "Content-Type: application/json" \
  -d "{\"invoice\": $(cat examples/belgium_valid_invoice.json)}"
```

Mock webhook test:

```bash
curl -s -X POST "$BASE_URL/v1/webhooks/test" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"invoice_id":"REPLACE_ME","target_url":"https://example.test/webhook"}'
```
