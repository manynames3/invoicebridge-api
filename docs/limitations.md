# Limitations

This repository is a sandbox MVP, not a certified e-invoicing network service.

## Compliance

- XML output is UBL-like and Peppol-inspired, not official schema-validated UBL.
- No real Peppol access point is integrated.
- No tax authority or government platform submission is performed.
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
