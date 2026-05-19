# ADR 0003: Use Deterministic Mock Providers For The MVP

## Status

Accepted

## Context

Real Peppol delivery, certified XRechnung conformance, KSeF submission, ANAF/SPV submission, and Spanish SIF/VERI*FACTU integrations require provider credentials, official schemas, conformance testing, operational controls, and legal/compliance review. The MVP should demonstrate routing architecture without claiming production certification.

## Decision

Implement deterministic mock providers for Peppol-style submission, customer-managed Germany delivery, Poland KSeF sandbox submission, Romania ANAF sandbox submission, and Spain local fiscal-record evidence.

## Consequences

- The end-to-end workflow can be tested without external network dependencies.
- Provider references and statuses are stable enough for automated tests.
- The README and limitations must clearly state that this is not certified Peppol delivery, official XRechnung conformance, KSeF submission, ANAF/SPV submission, AEAT submission, or VERI*FACTU certification.
