# InvoiceBridge API

InvoiceBridge API is a production-style FastAPI backend that accepts normalized invoice JSON, checks a Belgium B2B Peppol-style mandate profile, validates totals and tax rules, transforms valid invoices into sandbox UBL-like XML, simulates network submission, tracks status, and stores an audit trail. It is designed as a B2B infrastructure API for ERP, accounting SaaS, billing platforms, marketplaces, and cross-border sellers that need e-invoicing compliance workflows without replacing their existing invoice system.

This is a portfolio MVP, not a certified e-invoicing gateway. The Belgium/Peppol implementation is intentionally sandboxed and mock-routed.

Live landing page: [https://invoicebridge-api.pages.dev](https://invoicebridge-api.pages.dev)

## About

The project models the core workflow of an e-invoicing compliance provider:

Existing invoice JSON -> mandate profile -> validation -> UBL-like transformation -> mock Peppol routing -> status tracking -> audit evidence.

The first supported profile is `BE_B2B_PEPPOL_MVP`, a Belgium B2B profile inspired by Peppol BIS Billing 3.0. The code is structured so future country profiles such as Poland KSeF or a real Peppol access point can be added behind the same validation, transformation, provider, and audit boundaries.

Local OpenAPI docs are available at [http://localhost:8000/docs](http://localhost:8000/docs) after starting the API.

## Tech Stack

- Python 3.12
- FastAPI and Pydantic v2
- SQLAlchemy 2 and Alembic
- PostgreSQL via Docker Compose; SQLite-supported defaults for local/test convenience
- Uvicorn
- pytest, ruff, mypy
- Docker, Docker Compose
- GitHub Actions CI

## Engineering Highlights

- Modular country/profile design with validator, transformer, and provider registries.
- Belgium B2B validation for required parties, VAT IDs, buyer routing ID, supported currency, allowed VAT rates, line totals, tax totals, and payable total consistency.
- UBL-like XML generation using structured XML APIs instead of string assembly.
- Provider abstraction with deterministic `MockPeppolProvider` submission outcomes.
- Idempotency support for transform/send flows.
- Persistent invoice, submission, validation result, and audit event models.
- Audit trail events include SHA-256 hashes of relevant payloads where practical.
- API key authentication for `/v1` endpoints, request/correlation IDs, JSON structured logging, VAT ID masking in audit metadata, and payload size checks.
- OpenAPI tags/descriptions, examples, Dockerized runtime, Alembic migrations, and CI lint/type/test workflow.

## MVP Scope

The first supported profile is `BE_B2B_PEPPOL_MVP`:

- Country: Belgium (`BE`)
- Transaction type: `B2B`
- Required format: `PEPPOL_BIS_BILLING_3_UBL_LIKE`
- Network: `PEPPOL_MOCK`
- Effective date: `2026-01-01`
- Buyer routing ID required
- Seller and buyer VAT IDs required
- Supported currency: `EUR`
- Allowed VAT rates: `0`, `6`, `12`, `21`
- Document totals are required and must match calculated line and tax totals.

## What It Does

- Checks supported countries and mandate metadata.
- Validates normalized invoice JSON with machine-readable error codes.
- Records failed transform attempts with `validation_failed` audit evidence.
- Transforms valid invoices into UBL-like XML inspired by Peppol BIS Billing 3.0.
- Stores invoice payloads, transformed XML, validation results, submissions, and audit events.
- Simulates provider submission through `MockPeppolProvider`.
- Tracks invoice status and exposes audit trail evidence hashes.

## What It Does Not Do

- It is not certified for real Peppol delivery.
- It does not submit to Belgian tax authorities.
- It does not perform official UBL schema validation.
- It does not provide legal advice or jurisdiction-specific compliance certification.
- It does not implement multi-tenant accounts, billing, real webhooks, or production retention policies yet.

This MVP produces UBL-like XML for sandbox/demo purposes. Production use would require official schema validation, certified access point integration, country-specific legal review, and conformance testing.

## Architecture

Architecture details are in [docs/architecture.md](docs/architecture.md), including a C4-style container diagram, runtime flow, deployment shape, and constraints.

Architecture decision records are in [docs/adrs](docs/adrs).

Core extension points:

- `app/services/validation/`: country/network validation profiles.
- `app/services/transform/`: invoice-to-document transformers.
- `app/services/providers/`: routing/submission provider abstraction.
- `app/services/*/registry.py`: dispatch supported profiles, formats, and networks.
- `app/services/country_profiles.py`: supported jurisdiction metadata.

## Project Structure

```text
app/
  api/routes/        FastAPI route modules
  core/              config, logging, auth, rate-limit placeholder
  db/                SQLAlchemy models, session, Alembic migrations
  schemas/           Pydantic request/response contracts
  services/          validation, transform, provider, invoice, audit logic
docs/
  adrs/              architecture decision records
examples/            sample Belgium invoice payloads and curl commands
site/                static sales landing page deployed to Cloudflare Pages
tests/               pytest coverage for validation, transform, send, audit
```

## Local Setup

```bash
python -m pip install -e ".[dev]"
cp .env.example .env
make run
```

The API runs at [http://localhost:8000](http://localhost:8000).

For Postgres-backed local development:

```bash
docker-compose up --build
```

The API container runs on port `8000`, and Postgres runs on port `5432`.

## Authentication

All `/v1` endpoints require:

```http
X-API-Key: local-dev-key
```

`GET /health` and `/docs` are public for local operations.

## API Examples

Validate:

```bash
curl -s -X POST http://localhost:8000/v1/invoices/validate \
  -H "X-API-Key: local-dev-key" \
  -H "Content-Type: application/json" \
  --data @examples/belgium_valid_invoice.json
```

Transform with idempotency:

```bash
curl -s -X POST http://localhost:8000/v1/invoices/transform \
  -H "X-API-Key: local-dev-key" \
  -H "Idempotency-Key: demo-transform-001" \
  -H "Content-Type: application/json" \
  --data @examples/belgium_valid_invoice.json
```

Send a payload through the mock provider:

```bash
curl -s -X POST http://localhost:8000/v1/invoices/send \
  -H "X-API-Key: local-dev-key" \
  -H "Idempotency-Key: demo-send-001" \
  -H "Content-Type: application/json" \
  -d "{\"invoice\": $(cat examples/belgium_valid_invoice.json)}"
```

Check status:

```bash
curl -s -H "X-API-Key: local-dev-key" \
  http://localhost:8000/v1/invoices/status/{invoice_id}
```

Audit trail:

```bash
curl -s -H "X-API-Key: local-dev-key" \
  http://localhost:8000/v1/invoices/{invoice_id}/audit-trail
```

More examples are in [docs/api_examples.md](docs/api_examples.md).

## Sample Validation Response

```json
{
  "compliant": true,
  "errors": [],
  "warnings": [],
  "normalized_totals": {
    "tax_exclusive_amount": "250.00",
    "tax_amount": "45.00",
    "tax_inclusive_amount": "295.00",
    "payable_amount": "295.00",
    "currency": "EUR"
  },
  "required_format": "PEPPOL_BIS_BILLING_3_UBL_LIKE",
  "country_profile_used": "BE_B2B_PEPPOL_MVP"
}
```

## Testing

```bash
make lint
make typecheck
make test
```

CI runs the same ruff, mypy, and pytest checks on GitHub Actions.

## Deployment

The API deployment model included in this repository is Docker Compose:

- `api`: FastAPI/Uvicorn application container.
- `db`: PostgreSQL 16 with a health check and persistent volume.

For production, the API should run migrations explicitly with Alembic, disable automatic table creation, terminate TLS at the platform edge or gateway, and source secrets from the deployment environment.

The public sales landing page is a static site in `site/` and is deployed separately on Cloudflare Pages at [https://invoicebridge-api.pages.dev](https://invoicebridge-api.pages.dev).

## Data Retention And Audit Trail

The MVP stores invoice payloads, transformed XML, validation results, provider responses, and audit events in the configured database. Audit events include metadata and SHA-256 hashes of relevant payloads where practical. Logs mask VAT IDs and avoid writing full invoice payloads at info level.

Production retention should be implemented per tenant, jurisdiction, customer contract, and data processing agreement. That work is intentionally not included in this MVP.

## Limitations

See [docs/limitations.md](docs/limitations.md) for compliance, security, and operations limitations.

## Roadmap

1. Real Peppol access point integration
2. Official UBL schema validation
3. Poland KSeF profile
4. Webhook delivery
5. Multi-tenant accounts
6. Usage-based billing/metering
7. Dashboard
8. Terraform/AWS deployment
