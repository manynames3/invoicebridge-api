# InvoiceBridge API

[![CI](https://github.com/manynames3/invoicebridge-api/actions/workflows/ci.yml/badge.svg)](https://github.com/manynames3/invoicebridge-api/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.12-3776AB)
![FastAPI](https://img.shields.io/badge/FastAPI-Pydantic%20v2-009688)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Docker%20Compose-4169E1)

InvoiceBridge API is a Germany-first FastAPI backend that turns existing invoice JSON into validated XRechnung-style structured XML, status records, tenant-scoped workflows, and audit evidence. It is designed as a compliance workflow layer for ERP, accounting SaaS, billing platforms, and B2B marketplaces that need e-invoicing readiness without replacing their billing system.

This is a portfolio-grade MVP, not a certified government submission gateway. Germany is usable only when generated invoices pass official XRechnung validation. Legal production support for Belgium, Poland, Romania, and Spain is coming soon after required access-point, tax-authority, signing, declaration, or conformance work is completed.

Live landing page: [https://invoicebridge-api.pages.dev](https://invoicebridge-api.pages.dev)

## At A Glance

| Area | What to know |
|---|---|
| Primary workflow | Invoice JSON -> country/profile validation -> XRechnung/structured XML -> status -> audit trail |
| First usable country path | Germany B2B XRechnung output with official-validator hook and customer-managed delivery |
| Intended buyer/user | Billing, ERP, marketplace, and accounting SaaS engineering or finance-ops teams |
| Backend stack | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy, Alembic, PostgreSQL, Docker |
| Product credibility | Tenant API keys, idempotency request hashing, official validation evidence, audit hashes, multi-region metadata, CI |
| Honest boundary | No certified Peppol/tax-authority submission, no legal advice, no self-serve billing yet |

## Reviewer Quick Links

- Product demo path: [examples/germany_demo.sh](examples/germany_demo.sh)
- Fast technical review path: [docs/reviewer_guide.md](docs/reviewer_guide.md)
- Architecture overview and C4 diagram: [docs/architecture.md](docs/architecture.md)
- Live demo talk track: [docs/demo_script.md](docs/demo_script.md)
- Production readiness guardrails: [docs/production_readiness.md](docs/production_readiness.md)
- Compliance and operations limitations: [docs/limitations.md](docs/limitations.md)
- Architecture decision records: [docs/adrs](docs/adrs)
- Pilot intake template: [.github/ISSUE_TEMPLATE/germany-pilot.yml](.github/ISSUE_TEMPLATE/germany-pilot.yml)

## Try The Germany Workflow

Run the API, then execute the focused demo script:

```bash
docker-compose up --build
```

In another terminal:

```bash
./examples/germany_demo.sh
```

The demo checks service health, lists Germany production-readiness blockers, creates a demo tenant with a tenant-scoped API key, validates `examples/germany_valid_invoice.json`, transforms it into XRechnung UBL, runs the configured official validator command, then returns status and audit trail evidence.

For local Python development:

```bash
python3 -m pip install -e ".[dev]"
cp .env.example .env
docker-compose up -d db
make run
./examples/germany_demo.sh
```

`.env.example` points at the Docker Compose Postgres database. If you run the API directly with `make run`, start Postgres first with `docker-compose up -d db`, or override `DATABASE_URL=sqlite:///./invoicebridge.db` for a local SQLite demo.

Local OpenAPI docs are available at [http://localhost:8000/docs](http://localhost:8000/docs) after starting the API.

## About

The project models the core workflow of an e-invoicing compliance provider:

Existing invoice JSON -> mandate profile -> validation -> structured transformation -> mock routing or local evidence record -> status tracking -> audit evidence.

The current paid-MVP direction is Germany XRechnung validation and evidence for teams that already produce invoice JSON. Belgium, Poland, Romania, and Spain remain implemented evaluation profiles and roadmap signals, not production claims. The code is structured so future country profiles or a real Peppol/government-platform adapter can be added behind the same validation, transformation, provider, and audit boundaries.

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
- Idempotency support for transform/send flows, including request-hash checks that reject accidental key reuse with a different payload.
- Persistent invoice, submission, validation result, and audit event models.
- Audit trail events include SHA-256 hashes of relevant payloads where practical.
- Official validator command results are persisted with document hashes and audit events.
- Region-aware tenant routing with tenant home region, data-residency region, and failover region metadata.
- Multi-region runtime metadata with `/health/ready`, `/v1/regions`, `/v1/tenants`, regional response headers, and persisted processing regions on invoice/submission/audit records.
- Standby-region write protection rejects new invoice mutations unless the deployment role is `local`, `primary`, or `active`.
- Admin and tenant-scoped API key authentication for `/v1` endpoints, request/correlation IDs, JSON structured logging, VAT ID masking in audit metadata, and payload size checks.
- Invoice archive/redaction endpoint that removes stored invoice payload/XML while preserving audit hashes.
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
- Runs a configured official validator command and persists the validation result, document hash, and audit evidence.
- Exposes production-readiness guardrails so evaluation-only profiles are not misrepresented as legal production integrations.
- Simulates provider submission or local evidence recording through deterministic mock providers.
- Tracks invoice status and exposes audit trail evidence hashes.

## What It Does Not Do

- It is not certified for real Peppol delivery.
- It does not submit to Belgian, Polish, Romanian, Spanish, German, or EU tax authority systems.
- It does not guarantee official UBL, XRechnung, KSeF, RO e-Factura, Peppol, VERI*FACTU, or Spain B2B platform conformance unless the relevant official validator/integration is configured and passing.
- It does not provide legal advice or jurisdiction-specific compliance certification.
- It does not implement self-serve billing, real webhooks, automated retention schedules, or production legal/compliance policy management yet.

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

Recommended demo runtime:

```bash
docker-compose up --build
```

The API container runs on port `8000`, and Postgres runs on port `5432`.

Python-only local development:

```bash
python3 -m pip install -e ".[dev]"
cp .env.example .env
docker-compose up -d db
make run
```

The API runs at [http://localhost:8000](http://localhost:8000).

## Authentication

All `/v1` endpoints require an API key:

```http
X-API-Key: local-dev-key
```

The local `API_KEY` is the admin key used for setup tasks such as creating tenants. `POST /v1/tenants` returns a tenant API key once; tenant keys are stored hashed and can only access that tenant's invoice workflows.

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

Focused Germany demo:

```bash
./examples/germany_demo.sh
```

Suggested talk track for a live demo is in [docs/demo_script.md](docs/demo_script.md).

Create a tenant and receive a tenant-scoped API key. The key is returned once and stored hashed:

```bash
curl -s -X POST http://localhost:8000/v1/tenants \
  -H "X-API-Key: local-dev-key" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"acme-eu","name":"Acme EU","home_region":"local-dev","data_residency_region":"EU","failover_region":"local-standby"}'
```

Archive and redact an invoice while keeping audit evidence:

```bash
curl -s -X POST http://localhost:8000/v1/invoices/{invoice_id}/archive \
  -H "X-API-Key: {tenant_api_key}" \
  -H "Content-Type: application/json" \
  -d '{"reason":"customer retention request"}'
```

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

## Monetization Direction

The practical first paid offer is an assisted Germany XRechnung pilot for a billing, ERP, accounting SaaS, or marketplace team:

- Customer sends real invoice JSON examples.
- InvoiceBridge validates required XRechnung fields, totals, VAT IDs, and payment metadata.
- InvoiceBridge generates XRechnung UBL and stores document hashes, official-validator results, status, and audit events.
- The customer keeps delivery/customer routing under their existing process until a production delivery integration is needed.

Suggested pilot packaging: setup plus monthly API/support fee. Full self-serve billing, key rotation UI, webhook delivery, automated retention schedules, and production policy management remain roadmap work.

Pilot intake is captured through the [Germany XRechnung pilot issue template](.github/ISSUE_TEMPLATE/germany-pilot.yml), which asks for workflow, volume, pain point, and sanitized payload shape without requesting sensitive invoice data.

## Data Retention And Audit Trail

The MVP stores invoice payloads, transformed XML, validation results, provider responses, official-validator results, and audit events in the configured database. Audit events include metadata and SHA-256 hashes of relevant payloads where practical. Logs mask VAT IDs and avoid writing full invoice payloads at info level.

For customer-controlled cleanup, `POST /v1/invoices/{invoice_id}/archive` marks an invoice archived and redacts the stored original payload and transformed XML by default while preserving audit hashes. Automated retention schedules should still be implemented per tenant, jurisdiction, customer contract, and data processing agreement before broader production rollout.

Do not put sensitive production invoice data into an unreviewed public demo deployment. Use local examples or customer-approved test payloads until tenant-scoped API keys, retention terms, and privacy terms are configured for that deployment.

## Limitations

See [docs/limitations.md](docs/limitations.md) for compliance, security, and operations limitations.

## Roadmap

1. Real Peppol access point integration
2. Official UBL schema validation
3. Official XRechnung, KSeF, RO e-Factura, and Spain SIF/VERI*FACTU conformance adapters
4. Real KSeF and ANAF/SPV credential flows
5. Webhook delivery
6. Tenant account management, key rotation, and audit exports
7. Usage-based billing/metering
8. Dashboard
9. Terraform/AWS deployment
