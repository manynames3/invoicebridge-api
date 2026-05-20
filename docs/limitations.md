# Limitations

This repository is an MVP, not a certified e-invoicing network service.

## Compliance

- Current production status by implemented profile:
  - Belgium: legal production support coming soon.
  - Germany: usable only when invoice-by-invoice official validation passes.
  - Poland: legal production support coming soon.
  - Romania: legal production support coming soon.
  - Spain: legal production support coming soon after external signing, AEAT test evidence, declaration, and legal review are complete.
- Germany XML is generated as XRechnung 3.0 UBL and must pass the configured KoSIT validator before production reliance.
- Belgium/Romania XML is UBL-like and Poland XML is KSeF-like; those are not official schema-validated Peppol, RO e-Factura, or KSeF outputs. Spain now emits AEAT-shaped `RegFactuSistemaFacturacion` XML and can be checked with downloaded AEAT XSD assets, but it is still not a completed certified SIF/VERI*FACTU product.
- National tax ID validation includes local checksum checks where implemented, but does not perform VAT registry lookups or prove legal registration status.
- No real Peppol access point is integrated.
- No tax authority or government platform submission is performed.
- Production-readiness endpoints report missing official validators, API configuration, credentials, signing, and declaration steps rather than treating a mock workflow as legal compliance.
- Germany is modeled as customer-managed delivery, not central clearance; certified production use still requires a passing official validator result and customer review.
- Poland is modeled with a deterministic KSeF mock provider boundary, not production KSeF authentication, submission, or UPO receipt handling.
- Romania is modeled with a deterministic ANAF mock provider boundary, not SPV OAuth, ANAF submission, signed response downloads, or production RO_CIUS conformance.
- Spain is modeled as local SIF record-integrity evidence with required producer/software identity, VERI*FACTU capability metadata, event-log metadata, AEAT `RegistroAlta` output, SHA-256 record/event hashes, tax breakdowns, signing hook, and QR payload draft data; it is not AEAT submission, certified SIF compliance, or production VERI*FACTU.
- Spain production readiness still depends on official AEAT schemas/WSDLs, signing policy, external test-portal evidence, and a responsible declaration for the deployed software version.
- Mandate metadata is static MVP configuration, not legal advice.
- Country-specific legal review and conformance testing are required before production use.

## Security

- API key auth supports one admin key plus tenant-scoped keys stored as SHA-256 hashes. A production deployment should still add key rotation, expiration, per-key permissions, and stronger secret-management controls.
- Tenant-scoped invoice authorization is implemented for invoice writes, status, documents, official validation, archive/redaction, and audit trail reads.
- Rate limiting is represented by an interface and no-op implementation.
- Secrets are expected through environment variables and are not stored in code.

## Operations

- Webhooks are recorded as mock audit events; no outbound delivery is attempted.
- Invoice archive/redaction is implemented for customer-initiated cleanup of stored payload/XML while preserving audit hashes. Automated retention schedules are not implemented.
- Observability is limited to structured logs, request IDs, persisted invoice events, and persisted official-validator results.
- Multi-region support is an application-level design and local simulation; production still needs managed database replication, failover automation, regional secrets, and centralized observability.
- Auto table creation is enabled for MVP convenience; production should run migrations explicitly.
- Payload size enforcement relies on `Content-Length`; production should also enforce streamed body limits at the gateway/app server layer.
