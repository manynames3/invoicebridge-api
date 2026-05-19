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
```

Validate:

```bash
curl -s -X POST "$BASE_URL/v1/invoices/validate" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  --data @examples/belgium_valid_invoice.json
```

Transform:

```bash
curl -s -X POST "$BASE_URL/v1/invoices/transform" \
  -H "X-API-Key: $API_KEY" \
  -H "Idempotency-Key: transform-demo-001" \
  -H "Content-Type: application/json" \
  --data @examples/belgium_valid_invoice.json
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
