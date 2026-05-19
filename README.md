# InvoiceBridge API

InvoiceBridge API is a production-style FastAPI backend that accepts normalized invoice JSON, selects a country mandate profile, validates totals and tax rules, transforms valid invoices into sandbox structured outputs, simulates routing or local evidence recording, tracks status, and stores an audit trail. It is designed as a B2B infrastructure API for ERP, accounting SaaS, billing platforms, marketplaces, and cross-border sellers that need e-invoicing compliance workflows without replacing their existing invoice system.

This is a portfolio MVP, not a certified e-invoicing gateway. The Belgium, Germany, and Spain profiles are intentionally sandboxed and do not perform official network or tax-authority submission.

Live landing page: [https://invoicebridge-api.pages.dev](https://invoicebridge-api.pages.dev)

## About

The project models the core workflow of an e-invoicing compliance provider:

Existing invoice JSON -> mandate profile -> validation -> structured transformation -> mock routing or local evidence record -> status tracking -> audit evidence.

The supported MVP profiles are Belgium B2B Peppol-style, Germany EN 16931/XRechnung-style, and Spain NON-VERI*FACTU-style local fiscal-record evidence. The code is structured so future country profiles such as Poland KSeF or a real Peppol access point can be added behind the same validation, transformation, provider, and audit boundaries.

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
- Germany B2B no-network validation for German VAT IDs, EUR invoices, EN 16931/XRechnung-style output, and customer-managed delivery evidence.
- Spain B2B local fiscal-record validation for Spanish VAT/NIF IDs, EUR invoices, allowed VAT rates, record hash metadata, and NON-VERI*FACTU-style sandbox output.
- XML generation using structured XML APIs instead of string assembly.
- Provider abstraction with deterministic Peppol-style, customer-managed, and local-record mock outcomes.
- Idempotency support for transform/send flows.
- Persistent invoice, submission, validation result, and audit event models.
- Audit trail events include SHA-256 hashes of relevant payloads where practical.
- Region-aware tenant routing with tenant home region, data-residency region, and failover region metadata.
- Multi-region runtime metadata with `/health/ready`, `/v1/regions`, `/v1/tenants`, regional response headers, and persisted processing regions on invoice/submission/audit records.
- Standby-region write protection rejects new invoice mutations unless the deployment role is `local`, `primary`, or `active`.
- API key authentication for `/v1` endpoints, request/correlation IDs, JSON structured logging, VAT ID masking in audit metadata, and payload size checks.
- OpenAPI tags/descriptions, examples, Dockerized runtime, Alembic migrations, and CI lint/type/test workflow.

## MVP Scope

Supported MVP profiles:

- `BE_B2B_PEPPOL_MVP`: Belgium B2B Peppol-style sandbox profile, `PEPPOL_BIS_BILLING_3_UBL_LIKE`, `PEPPOL_MOCK`, buyer routing ID required, VAT rates `0`, `6`, `12`, `21`.
- `DE_B2B_EN16931_MVP`: Germany B2B no-network sandbox profile, `XRECHNUNG_EN16931_UBL_LIKE`, `CUSTOMER_MANAGED_DELIVERY_MOCK`, German VAT IDs required, VAT rates `0`, `7`, `19`.
- `ES_B2B_NON_VERIFACTU_MVP`: Spain B2B local fiscal-record sandbox profile, `NON_VERIFACTU_FISCAL_RECORD_XML_LIKE`, `LOCAL_FISCAL_RECORD_MOCK`, Spanish VAT/NIF IDs required, VAT rates `0`, `4`, `10`, `21`.

All profiles currently support `EUR` and require document totals that match calculated line and tax totals.

## What It Does

- Checks supported countries and mandate metadata.
- Validates normalized invoice JSON with machine-readable error codes.
- Records failed transform attempts with `validation_failed` audit evidence.
- Transforms valid Belgium and Germany invoices into UBL-like XML inspired by EN 16931 profile structures.
- Transforms valid Spain invoices into sandbox local fiscal-record XML-like evidence with current-record hashing.
- Stores invoice payloads, transformed XML, validation results, submissions, and audit events.
- Simulates provider submission or local evidence recording through deterministic mock providers.
- Tracks invoice status and exposes audit trail evidence hashes.

## What It Does Not Do

- It is not certified for real Peppol delivery.
- It does not submit to Belgian, German, Spanish, or EU tax authority systems.
- It does not perform official UBL, XRechnung, Peppol, VERI*FACTU, or Spain B2B platform conformance validation.
- It does not provide legal advice or jurisdiction-specific compliance certification.
- It does not implement tenant-scoped authentication, billing, real webhooks, or production retention policies yet.

This MVP produces UBL-like XML and fiscal-record XML-like output for sandbox/demo purposes. Production use would require official schema validation, certified provider or platform integration where applicable, country-specific legal review, and conformance testing.

## Architecture

Architecture details are in [docs/architecture.md](docs/architecture.md), including a C4-style container diagram, runtime flow, deployment shape, and constraints.

The multi-region deployment model is documented in [docs/multi_region.md](docs/multi_region.md). It intentionally uses a single-cloud, multi-region design before multi-cloud: tenant home-region routing, regional-primary writes, standby failover, idempotent retries, and audit evidence with processing-region metadata.

AWS and GCP deployment patterns are summarized in [docs/cloud_deployment_patterns.md](docs/cloud_deployment_patterns.md).

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
examples/            sample Belgium, Germany, and Spain invoice payloads and curl commands
scripts/             smoke checks for local multi-region runtime
site/                static sales landing page deployed to Cloudflare Pages
tests/               pytest coverage for validation, transform, send, audit
docker-compose.multi-region.yml  local two-region simulation with separate Postgres databases
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

Validate Germany and Spain no-network profiles:

```bash
curl -s -X POST http://localhost:8000/v1/invoices/validate \
  -H "X-API-Key: local-dev-key" \
  -H "Content-Type: application/json" \
  --data @examples/germany_valid_invoice.json

curl -s -X POST http://localhost:8000/v1/invoices/validate \
  -H "X-API-Key: local-dev-key" \
  -H "Content-Type: application/json" \
  --data @examples/spain_valid_invoice.json
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

Region topology:

```bash
curl -s -H "X-API-Key: local-dev-key" \
  http://localhost:8000/v1/regions
```

Register a tenant routing policy:

```bash
curl -s -X POST http://localhost:8000/v1/tenants \
  -H "X-API-Key: local-dev-key" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"acme-eu","name":"Acme EU","home_region":"local-dev","data_residency_region":"EU","failover_region":"local-standby"}'
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

For a local multi-region simulation:

```bash
make docker-multiregion-up
curl -s http://localhost:8001/health/ready
curl -s http://localhost:8002/health/ready
make smoke-multiregion
make docker-multiregion-down
```

The production recommendation is regional-primary writes with a standby region, not active-active database writes. See [docs/multi_region.md](docs/multi_region.md).

## Multi-Region / Cloud Deployment Skills

- AWS pattern: ECS Fargate or App Runner, ECR, RDS PostgreSQL, Route 53/Global Accelerator failover, Secrets Manager, CloudWatch.
- GCP pattern: Cloud Run, Artifact Registry, Cloud SQL PostgreSQL, External HTTP(S) Load Balancer or DNS failover, Secret Manager, Cloud Logging/Monitoring.
- Shared platform practices: Docker image portability, environment-driven config, explicit Alembic migrations, health/readiness checks, smoke tests, tenant home-region routing, idempotency-safe retries, and regional audit evidence.

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
4. Official XRechnung and Spain SIF/VERI*FACTU conformance adapters
5. Webhook delivery
6. Tenant-scoped auth and account management
7. Usage-based billing/metering
8. Dashboard
9. Terraform/AWS deployment
