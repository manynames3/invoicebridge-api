# ADR 0010: Treat Spain SIF As A Readiness Boundary, Not A Certification Claim

## Status

Accepted

## Context

Spain SIF / VERI*FACTU readiness is not just a tax-ID validation or XML formatting problem. The system must model official registration-record fields, hash chaining, QR data, event logging, signing, responsible-declaration evidence, and AEAT testing without claiming that the repository itself is certified.

## Decision

Implement a Spain SIF path with explicit guardrails while reporting legal production support as coming soon:

- Generate AEAT-shaped `RegFactuSistemaFacturacion` XML with `RegistroAlta` fields for issuer NIF, invoice series/number, issue date, invoice type, total tax, total amount, previous hash, and timestamp.
- Generate SHA-256 record and event hashes over explicit field subsets.
- Generate QR payload draft data without embedding the record hash.
- Require software producer/system metadata, VERI*FACTU capability, event-log metadata, and previous hash-chain values at validation time.
- Provide an AEAT WSDL/XSD asset setup script and local `xmllint` validation command.
- Provide a signing command interface and responsible-declaration draft endpoint without bundling certificate material or legal assertions.
- Keep production readiness false until official validator, signing, immutable event log, AEAT test evidence, VERI*FACTU submission capability, and responsible declaration flags are configured.

## Consequences

- The Spain profile is more credible for technical review because it models the real compliance surface instead of a generic local record.
- The API still does not claim AEAT certification or production legal compliance.
- Future work can replace the XML-like output with official AEAT XSD/WSDL integration behind the same validation, transform, provider, and audit boundaries.
