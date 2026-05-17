# Architecture

InvoiceBridge API is a modular FastAPI service for the e-invoicing compliance workflow: accept normalized invoice JSON, select a country mandate profile, validate compliance rules, transform valid invoices into sandbox UBL-like XML, submit through a mock network provider, track status, and persist an audit trail.

The MVP intentionally supports one jurisdiction/profile: Belgium B2B Peppol-style invoicing through `BE_B2B_PEPPOL_MVP`. The design keeps mandate rules, validators, transformers, and providers separate so additional countries or real network providers can be added without rewriting the HTTP API.

## C4-Style Container Diagram

```mermaid
flowchart TB
  actor["API Client\nERP, billing system, marketplace"]

  subgraph app["InvoiceBridge API Container\nFastAPI + Uvicorn"]
    routes["API Routes\nhealth, countries, mandates, invoices, webhooks"]
    service["InvoiceService\nworkflow orchestration"]
    profiles["Country Profile Registry\nBE_B2B_PEPPOL_MVP"]
    validators["Validation Registry\nBEPeppolMVPValidator"]
    transformers["Transform Registry\nUBLLikeTransformer"]
    providers["Provider Registry\nMockPeppolProvider"]
    audit["Audit Service\npayload hashes + event metadata"]
  end

  db[("PostgreSQL\ninvoices, submissions, validation results, audit events")]
  mock["Mock Peppol Network\nsandbox provider response"]
  docs["OpenAPI Docs\n/docs"]

  actor -->|"HTTPS/JSON + X-API-Key"| routes
  routes --> service
  routes --> docs
  service --> profiles
  service --> validators
  service --> transformers
  service --> providers
  service --> audit
  service --> db
  audit --> db
  providers --> mock
```

## Runtime Flow

1. Client sends normalized invoice JSON to `/v1/invoices/validate`, `/transform`, or `/send`.
2. API key middleware protects `/v1` routes and request middleware attaches an `X-Request-ID`.
3. `InvoiceService` selects the validator through `validation/registry.py`.
4. `BEPeppolMVPValidator` checks required fields, VAT IDs, buyer routing ID, currency, VAT rates, line amounts, tax totals, and payable total consistency.
5. On validation failure, the service records an invoice record plus `invoice_received` and `validation_failed` audit events.
6. On validation success, the transformer registry selects `UBLLikeTransformer`, which creates sandbox XML using `xml.etree.ElementTree`.
7. Transform and validation outputs are persisted with audit events and SHA-256 payload hashes.
8. `/send` resolves an existing invoice or first transforms a payload, then uses `MockPeppolProvider` through the provider registry.
9. Provider responses update invoice delivery status and create `submitted`, `accepted`, `rejected`, `pending`, or `retried` audit events.
10. `/status/{invoice_id}` and `/{invoice_id}/audit-trail` expose operational state and chronological evidence.

## Deployment Shape

The included deployment model is Docker Compose:

- `api`: Python 3.12 slim image running Uvicorn and the FastAPI app.
- `db`: PostgreSQL 16 Alpine with a health check and persistent volume.
- Configuration is environment-driven through `pydantic-settings`.
- Alembic migrations are present; local Compose uses `AUTO_CREATE_TABLES=true` for MVP convenience.

For a production-like deployment, run Alembic migrations explicitly, set `AUTO_CREATE_TABLES=false`, inject secrets through the platform, and put TLS, request body limits, and rate limiting at the edge/gateway as well as in the app.

## Key Constraints

- The XML output is UBL-like and Peppol-inspired, not official schema-validated UBL.
- The provider is a deterministic mock provider, not a certified Peppol access point.
- The API currently has one static country profile and no tenant/account model.
- API key auth is intentionally basic for the MVP.
- Payload size enforcement relies on `Content-Length`; production should also enforce streamed body limits upstream.
- Audit hashes support integrity checks but are not a full non-repudiation or legal archiving system.

## Extension Points

- Add mandate metadata in `app/services/country_profiles.py`.
- Add country validators in `app/services/validation/` and register them in `validation/registry.py`.
- Add format transformers in `app/services/transform/` and register them in `transform/registry.py`.
- Add routing/submission providers in `app/services/providers/` and register them in `providers/registry.py`.
- Keep route contracts stable by returning the same validation, transform, send, status, and audit response schemas.

## Primary Modules

- `app/api/routes`: HTTP endpoints and OpenAPI metadata.
- `app/schemas`: Pydantic request/response contracts.
- `app/db`: SQLAlchemy models, session factory, and Alembic migrations.
- `app/services/invoices.py`: workflow orchestration, idempotency, status, and audit coordination.
- `app/services/validation`: compliance validation rules.
- `app/services/transform`: structured e-invoice document generation.
- `app/services/providers`: network/provider abstraction.
- `app/services/audit.py`: audit event creation and payload hashing.
