# Limitations

This repository is a sandbox MVP, not a certified e-invoicing network service.

## Compliance

- XML output is UBL-like, KSeF-like, or fiscal-record XML-like, not official schema-validated UBL, XRechnung, KSeF, RO e-Factura, Peppol, VERI*FACTU, or Spain B2B platform output.
- National tax ID validation includes local checksum checks where implemented, but does not perform VAT registry lookups or prove legal registration status.
- No real Peppol access point is integrated.
- No tax authority or government platform submission is performed.
- Production-readiness endpoints report missing official validators, API configuration, credentials, signing, and declaration steps rather than treating sandbox success as legal compliance.
- Germany is modeled as customer-managed delivery, not central clearance or certified XRechnung conformance.
- Poland is modeled with a deterministic KSeF sandbox provider boundary, not production KSeF authentication, submission, or UPO receipt handling.
- Romania is modeled with a deterministic ANAF sandbox provider boundary, not SPV OAuth, ANAF submission, signed response downloads, or production RO_CIUS conformance.
- Spain is modeled as local fiscal-record evidence only, not AEAT submission, certified SIF compliance, or production VERI*FACTU.
- Mandate metadata is static MVP configuration, not legal advice.
- Country-specific legal review and conformance testing are required before production use.

## Security

- API key auth is basic and suitable only for local/demo usage.
- Tenant routing metadata is implemented, but tenant-scoped authentication and authorization boundaries are not.
- Rate limiting is represented by an interface and no-op implementation.
- Secrets are expected through environment variables and are not stored in code.

## Operations

- Webhooks are recorded as mock audit events; no outbound delivery is attempted.
- Data retention policies are documented conceptually but not enforced.
- Observability is limited to structured logs and request IDs.
- Multi-region support is an application-level design and local simulation; production still needs managed database replication, failover automation, regional secrets, and centralized observability.
- Auto table creation is enabled for MVP convenience; production should run migrations explicitly.
- Payload size enforcement relies on `Content-Length`; production should also enforce streamed body limits at the gateway/app server layer.
