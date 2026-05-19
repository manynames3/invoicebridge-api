# ADR 0009: Production Readiness Guardrails

## Status

Accepted

## Context

Evaluation validation and mock submission are useful for demos, but they are not enough for a customer to rely on the API for legal e-invoicing mandates. Germany, Poland, Romania, and Spain each require official validation, credentials, signatures, receipts, declarations, or country-specific evidence before production reliance.

## Decision

InvoiceBridge exposes production-readiness checks and official-validator command hooks instead of treating mock workflow success as production compliance. The API reports missing blockers for each country and runs configured validator commands against transformed XML artifacts when provided.

## Consequences

- The product is more honest: mock provider success cannot be mistaken for legal compliance.
- No-paid-provider country paths can still be implemented with customer-provided credentials and official tooling.
- Production readiness depends on deployment configuration and customer compliance work, not only repository code.
- Future real providers can reuse the same readiness checks before enabling production sends.
