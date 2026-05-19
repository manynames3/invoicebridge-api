# ADR 0008: Model Direct Government Platform Profiles As Sandboxes

## Status

Accepted

## Context

Poland KSeF and Romania RO e-Factura are not Peppol access-point problems. They are government-platform integrations where production use depends on country credentials, authorization flows, official schemas, validation services, receipt handling, and operational controls.

## Decision

Add Poland and Romania as sandbox profiles behind the existing validator, transformer, provider, status, and audit contracts:

- `PL_B2B_KSEF_MVP` validates Polish NIP identifiers with checksum logic, supports PLN/EUR invoices, generates FA(3)-inspired XML-like output, and records deterministic KSeF sandbox provider references.
- `RO_B2B_EFACTURA_MVP` validates Romanian VAT/CUI checksums, supports RON/EUR invoices, generates RO_CIUS/UBL 2.1-inspired XML-like output, and records deterministic ANAF sandbox provider references.

## Consequences

- The API shows the real integration boundary without incurring paid access point or provider costs.
- Production KSeF and ANAF/SPV submission remain explicit future work.
- Tests can verify validation, transformation, idempotency, provider status, and audit behavior without external credentials.
