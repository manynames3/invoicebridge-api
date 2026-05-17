# ADR 0003: Use A Mock Peppol Provider For The MVP

## Status

Accepted

## Context

Real Peppol delivery requires certified access point integration, conformance testing, operational credentials, and legal/compliance review. The MVP should demonstrate routing architecture without claiming production certification.

## Decision

Implement `MockPeppolProvider` with deterministic accepted, rejected, and pending outcomes.

## Consequences

- The end-to-end workflow can be tested without external network dependencies.
- Provider references and statuses are stable enough for automated tests.
- The README and limitations must clearly state that this is not certified Peppol delivery.
