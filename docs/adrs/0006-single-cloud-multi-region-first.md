# ADR 0006: Use Single-Cloud Multi-Region Before Multi-Cloud

## Status

Accepted

## Context

InvoiceBridge API handles invoice payloads, delivery status, and audit evidence. The most realistic customer requirements are regional availability, data residency, retry safety, and audit continuity. Multi-cloud can be valuable for procurement, sovereignty, or vendor-risk reasons, but it adds duplicate IAM, networking, database, observability, secrets, and deployment complexity.

The MVP does not yet have a customer requirement that justifies operating the same workload across multiple cloud providers.

## Decision

The project will model a single-cloud, multi-region architecture first:

- Same Dockerized FastAPI app in multiple regions.
- Regional-primary writes, not active-active database writes.
- Tenant records carry home, data-residency, and failover regions for routing decisions.
- Managed PostgreSQL primary plus replica/promoted standby.
- Region identity exposed through health/readiness responses and headers.
- Invoice, submission, and audit records persist the processing region.
- Idempotency keys protect mutating invoice workflows during retries and failover.

## Consequences

This keeps the portfolio architecture credible and tied to customer needs. It demonstrates availability, data-residency thinking, failover, and operational evidence without overstating cloud portability.

The tradeoff is that the current design does not prove full multi-cloud operation. If a customer requires AWS/GCP/Azure portability later, the app remains portable through Docker, PostgreSQL, environment-based configuration, and OpenAPI contracts, but each cloud would need its own infrastructure, secrets, networking, and runbook work.
