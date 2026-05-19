# InvoiceBridge API

InvoiceBridge API is a production-style FastAPI backend that accepts normalized invoice JSON, selects a country mandate profile, validates totals and tax rules, transforms valid invoices into structured outputs, simulates routing or local evidence recording, tracks status, and stores an audit trail. It is designed as a B2B infrastructure API for ERP, accounting SaaS, billing platforms, marketplaces, and cross-border sellers that need e-invoicing compliance workflows without replacing their existing invoice system.

This is a portfolio MVP, not a certified e-invoicing gateway. Germany is usable only when generated invoices pass official XRechnung validation. Legal production support for Belgium, Poland, Romania, and Spain is coming soon after required access-point, tax-authority, signing, declaration, or conformance work is completed.

Live landing page: [https://invoicebridge-api.pages.dev](https://invoicebridge-api.pages.dev)

## About

The project models the core workflow of an e-invoicing compliance provider:

Existing invoice JSON -> mandate profile -> validation -> structured transformation -> mock routing or local evidence record -> status tracking -> audit evidence.

The supported MVP profiles are Belgium B2B Peppol-style, Germany XRechnung 3.0 UBL, Poland KSeF FA(3)-style, Romania RO e-Factura/RO_CIUS-style, and Spain NON-VERI*FACTU-style local SIF record-integrity evidence. The code is structured so future country profiles or a real Peppol/government-platform adapter can be added behind the same validation, transformation, provider, and audit boundaries.

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
- Germany B2B no-network validation for German VAT ID checksums, XRechnung-required business fields, EUR invoices, XRechnung 3.0 UBL output, local KoSIT validator setup, and customer-managed delivery evidence.
- Poland KSeF evaluation validation for Polish NIP checksum, PLN/EUR invoices, FA(3)-style output, and deterministic government-platform provider references.
- Romania RO e-Factura evaluation validation for Romanian VAT/CUI checksums, RON/EUR invoices, RO_CIUS/UBL 2.1-style output, and deterministic ANAF provider references.
- Spain B2B local SIF record validation for Spanish VAT/NIF/CIF checksums, EUR invoices, allowed VAT rates, producer/software identity, VERI*FACTU capability metadata, SHA-256 record/event chaining, AEAT `RegFactuSistemaFacturacion` / `RegistroAlta` XML output, tax breakdowns, and AEAT QR payload draft output.
- XML generation using structured XML APIs instead of string assembly.
- Provider abstraction with deterministic Peppol-style, customer-managed, government-platform, and local-record mock outcomes.
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

- `BE_B2B_PEPPOL_MVP`: legal production support coming soon. Peppol access point integration and conformance testing are roadmap work.
- `DE_B2B_EN16931_MVP`: usable only when official validation passes. Generates XRechnung 3.0 UBL and supports KoSIT validation, but each customer deployment still needs invoice-by-invoice validation and review.
- `PL_B2B_KSEF_MVP`: legal production support coming soon. Real KSeF API credentials, encryption, submission, and UPO handling are roadmap work.
- `RO_B2B_EFACTURA_MVP`: legal production support coming soon. Real ANAF/SPV OAuth, upload/status polling, and signed response handling are roadmap work.
- `ES_B2B_NON_VERIFACTU_MVP`: legal production support coming soon. Emits AEAT-shaped SIF XML and local evidence, but signing, AEAT test evidence, VERI*FACTU submission capability, and responsible declaration completion remain external blockers.

Belgium, Germany, and Spain currently support `EUR`. Poland supports `PLN` and `EUR`; Romania supports `RON` and `EUR`. All profiles require document totals that match calculated line and tax totals.

## Production Status By Country

| Country | Current status | What is still required |
|---|---|---|
| Belgium | Coming soon | Real Peppol access point, official conformance testing, and provider evidence. |
| Germany | Usable with official validation | XRechnung output must pass official validation for each customer payload; delivery remains customer-managed. |
| Poland | Coming soon | Real KSeF API authentication, encryption, production submission, and UPO receipt handling. |
| Romania | Coming soon | Real ANAF/SPV OAuth, upload/status polling, and official signed response handling. |
| Spain | Coming soon | Signing, immutable event logging, AEAT external test evidence, VERI*FACTU submission capability, responsible declaration, and legal review. |

## What It Does

- Checks supported countries and mandate metadata.
- Validates normalized invoice JSON with machine-readable error codes.
- Records failed transform attempts with `validation_failed` audit evidence.
- Transforms valid Germany invoices into XRechnung 3.0 UBL XML with the XRechnung CustomizationID.
- Transforms valid Belgium and Romania invoices into UBL-like XML inspired by Peppol/RO_CIUS profile structures.
- Transforms valid Poland invoices into KSeF FA(3)-style XML-like evaluation output.
- Transforms valid Spain invoices into AEAT-shaped local SIF `RegFactuSistemaFacturacion` XML with software identity, `RegistroAlta` fields, current/previous record hashing, event hashing, tax breakdowns, and QR payload draft data.
- Stores invoice payloads, transformed XML, validation results, submissions, and audit events.
- Exposes the stored transformed XML document with a document URL and SHA-256 hash for downstream export/testing.
- Exposes production-readiness guardrails so evaluation-only profiles are not misrepresented as legal production integrations.
- Simulates provider submission or local evidence recording through deterministic mock providers.
- Tracks invoice status and exposes audit trail evidence hashes.

## What It Does Not Do

- It is not certified for real Peppol delivery.
- It does not submit to Belgian, Polish, Romanian, Spanish, German, or EU tax authority systems.
- It does not guarantee official UBL, XRechnung, KSeF, RO e-Factura, Peppol, VERI*FACTU, or Spain B2B platform conformance unless the relevant official validator/integration is configured and passing.
- It does not provide legal advice or jurisdiction-specific compliance certification.
- It does not implement tenant-scoped authentication, billing, real webhooks, or production retention policies yet.

This MVP produces XRechnung UBL for Germany, AEAT-shaped local SIF record XML for Spain, and UBL-like/KSeF-like output for other evaluation profiles. Production use requires official schema validation, certified provider or platform integration where applicable, country-specific legal review, and conformance testing.

## Production Readiness Guardrails

More detail is in [docs/production_readiness.md](docs/production_readiness.md).

The API includes explicit checks for the no-paid-network production path:

- Germany can avoid a paid network provider, but must run official XRechnung/EN16931 validation such as KoSIT before a customer can rely on the output.
- Poland can use the direct KSeF government API path, but still needs official FA(3) validation, KSeF API configuration, encryption/authentication, and customer-provided credentials.
- Romania can use the direct ANAF/SPV path, but still needs RO_CIUS validation, ANAF API configuration, OAuth, upload/status polling, and signed response handling.
- Spain can use a local SIF/non-VERI*FACTU-style path with enforced software identity, VERI*FACTU capability metadata, record/event hash-chain evidence, and QR draft generation, but still needs official record validation, signing, immutable event logging, AEAT external test evidence, responsible-declaration readiness, and customer-specific compliance review.

Spain details are documented in [docs/spain_sif_readiness.md](docs/spain_sif_readiness.md).

Check blockers:

```bash
curl -s -H "X-API-Key: local-dev-key" \
  "http://localhost:8000/v1/compliance/production-readiness?country=DE&transaction_type=B2B"
```

Run a configured official validator command against a transformed document:

```bash
curl -s -X POST http://localhost:8000/v1/invoices/{invoice_id}/official-validate \
  -H "X-API-Key: local-dev-key"
```

Validator commands are configured through environment variables such as `XRECHNUNG_VALIDATOR_COMMAND`, `KSEF_SCHEMA_VALIDATOR_COMMAND`, `RO_EFACTURA_SCHEMA_VALIDATOR_COMMAND`, and `SPANISH_SIF_VALIDATOR_COMMAND`. Commands receive the XML file path as the final argument unless the command contains a `{xml}` placeholder. Spain production readiness also checks `SPANISH_SIF_SIGNING_COMMAND` or `SPANISH_SIF_SIGNING_CONFIGURED`, `SPANISH_SIF_EVENT_LOG_CONFIGURED`, `SPANISH_SIF_AEAT_TEST_PORTAL_VALIDATED`, `SPANISH_VERIFACTU_SUBMISSION_CAPABLE`, and `SPANISH_SIF_RESPONSIBLE_DECLARATION_READY`.

Set up the free KoSIT/XRechnung validator locally:

```bash
make setup-xrechnung-validator
export XRECHNUNG_VALIDATOR_COMMAND="vendor/xrechnung/validate-xrechnung.sh {xml}"
```

The Docker image installs Java and the KoSIT validator artifacts automatically, then sets `XRECHNUNG_VALIDATOR_COMMAND` for the container.

Set up the AEAT Spain SIF WSDL/XSD validator locally:

```bash
make setup-spanish-sif-assets
export SPANISH_SIF_VALIDATOR_COMMAND="vendor/spanish-sif/validate-spanish-sif.sh {xml}"
```

The Docker image installs `xmllint`, downloads the AEAT WSDL/XSD assets, and sets `SPANISH_SIF_VALIDATOR_COMMAND` for the container.

The sample Germany invoice in `examples/germany_valid_invoice.json` has been checked against KoSIT Validator `1.6.0` with XRechnung validator configuration `3.0.2` and accepted. Production use still requires validating each customer invoice.

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
examples/            sample Belgium, Germany, Poland, Romania, and Spain invoice payloads and curl commands
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

Validate no-paid-network/direct-government mock profiles:

```bash
curl -s -X POST http://localhost:8000/v1/invoices/validate \
  -H "X-API-Key: local-dev-key" \
  -H "Content-Type: application/json" \
  --data @examples/germany_valid_invoice.json

curl -s -X POST http://localhost:8000/v1/invoices/validate \
  -H "X-API-Key: local-dev-key" \
  -H "Content-Type: application/json" \
  --data @examples/poland_valid_invoice.json

curl -s -X POST http://localhost:8000/v1/invoices/validate \
  -H "X-API-Key: local-dev-key" \
  -H "Content-Type: application/json" \
  --data @examples/romania_valid_invoice.json

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

Download transformed XML:

```bash
curl -s -H "X-API-Key: local-dev-key" \
  http://localhost:8000/v1/invoices/{invoice_id}/document
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
3. Official XRechnung, KSeF, RO e-Factura, and Spain SIF/VERI*FACTU conformance adapters
4. Real KSeF and ANAF/SPV credential flows
5. Webhook delivery
6. Tenant-scoped auth and account management
7. Usage-based billing/metering
8. Dashboard
9. Terraform/AWS deployment
