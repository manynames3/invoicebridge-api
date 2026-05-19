# ADR 0003: Use Deterministic Mock Providers For The MVP

## Status

Accepted

## Context

Real Peppol delivery, certified XRechnung conformance, and Spanish SIF/VERI*FACTU integrations require provider credentials, conformance testing, operational controls, and legal/compliance review. The MVP should demonstrate routing architecture without claiming production certification.

## Decision

Implement deterministic mock providers for Peppol-style submission, customer-managed Germany delivery, and Spain local fiscal-record evidence.

## Consequences

- The end-to-end workflow can be tested without external network dependencies.
- Provider references and statuses are stable enough for automated tests.
- The README and limitations must clearly state that this is not certified Peppol delivery, official XRechnung conformance, AEAT submission, or VERI*FACTU certification.
