# Reviewer Guide

Use this page when evaluating the repository quickly as a backend/platform portfolio project.

## What This Is

InvoiceBridge API is a Germany-first e-invoicing workflow API. It accepts existing invoice JSON, validates country/profile rules, generates structured XML, records official-validator evidence when configured, tracks status, and preserves audit events.

The strongest current workflow is Germany XRechnung. Other country profiles are useful for evaluating the extension model, but they are documented as coming soon for legal production support.

## Five-Minute Review Path

1. Read the top of [README.md](../README.md) for product positioning and boundaries.
2. Start the API:

   ```bash
   docker-compose up --build
   ```

3. In another terminal, run the focused demo:

   ```bash
   ./examples/germany_demo.sh
   ```

4. Open local API docs:

   ```text
   http://localhost:8000/docs
   ```

5. Inspect these implementation areas:
   - `app/services/invoices.py`: workflow orchestration, idempotency, tenant scoping, audit coordination.
   - `app/services/validation/`: country/profile validation rules.
   - `app/services/transform/`: structured XML generation.
   - `app/services/providers/`: provider abstraction and deterministic mock boundaries.
   - `app/core/security.py`: admin and tenant API-key handling.
   - `tests/`: validation, transform, send, audit, official validation, and tenant authorization coverage.

## What Makes It Credible

- Clear separation between country profiles, validators, transformers, providers, and audit persistence.
- Germany XRechnung output path includes an official-validator command hook and persisted evidence.
- Tenant API keys are generated once, stored hashed, and scoped to tenant invoice workflows.
- Transform/send idempotency keys include request-hash checks to reject accidental key reuse with different payloads.
- Audit events include payload/document hashes where practical.
- Archive/redaction endpoint removes stored invoice payload/XML while preserving evidence hashes.
- Region-aware metadata models tenant home region, failover region, processing region, and standby write protection.
- Hosted demo database path uses Neon Postgres through `DATABASE_URL`; AWS production docs still point to RDS PostgreSQL.
- CI runs ruff, mypy, and pytest.

## What Is Intentionally Not Claimed

- No certified Peppol access point delivery.
- No live KSeF, ANAF, AEAT, or other tax-authority submission.
- No legal compliance certification.
- No self-serve billing or full account management.
- No production observability stack or automated retention scheduler.

## Best Demo Story

Position it as a workflow layer for billing platforms:

> "Your billing system already creates invoice data. InvoiceBridge validates the country rules, generates the structured document, stores validator evidence, and gives you status/audit APIs without forcing an ERP replacement."

Then show:

1. Tenant creation and tenant-scoped API key.
2. Germany invoice validation.
3. XRechnung transform.
4. Official validation result or explicit not-configured result.
5. Status response with validation evidence.
6. Audit trail.
7. Archive/redact endpoint.

## Best Next Build Phase

The next phase should stay narrow:

- Hosted demo backend with safe sample data.
- Neon-backed public demo deployment using migrated Postgres schema.
- Key rotation and per-key permissions.
- Real webhook delivery with signed callbacks.
- Germany-focused onboarding docs for mapping customer invoice JSON to the normalized schema.
- Production observability and retention schedule hooks.
