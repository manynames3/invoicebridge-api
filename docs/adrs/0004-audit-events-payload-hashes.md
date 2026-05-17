# ADR 0004: Persist Audit Events With Payload Hashes

## Status

Accepted

## Context

Compliance infrastructure APIs need traceability: what was received, how it validated, when it transformed, and how submission status changed. The MVP needs credible audit evidence without implementing a legal archive.

## Decision

Persist chronological `AuditEvent` records for invoice receipt, validation, transformation, submission, provider outcomes, retries, and mock webhooks. Store metadata plus SHA-256 hashes of relevant payloads where practical.

## Consequences

- Status and audit trail endpoints can show lifecycle evidence.
- Payload hashes support integrity checks and debugging.
- This does not replace production-grade retention, legal archiving, signing, or non-repudiation.
