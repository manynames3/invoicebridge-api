# ADR 0007: Model No-Network Country Profiles Explicitly

## Status

Accepted

## Context

Not every e-invoicing obligation starts as a central network submission problem. Germany B2B e-invoicing can be modeled as structured invoice generation with customer-managed delivery, while Spain has local fiscal-record integrity requirements that are separate from future B2B exchange platform routing.

## Decision

Add Germany and Spain as no-network MVP profiles with explicit mock provider networks:

- `DE_B2B_EN16931_MVP` validates German VAT ID checksums, XRechnung-required business fields, EUR invoices, and Germany VAT rates, then produces XRechnung 3.0 UBL XML for customer-managed delivery.
- `ES_B2B_NON_VERIFACTU_MVP` validates Spanish VAT/NIF/CIF checksums, EUR invoices, Spain VAT rates, required SIF/software metadata, and previous-record hash chaining, then produces NON-VERI*FACTU-style local SIF record XML-like evidence.

## Consequences

- The API can demonstrate multi-country compliance workflow value without pretending to submit to official systems.
- Each profile still uses the same validate, transform, send, status, and audit contracts.
- Documentation must keep these outputs labeled as sandbox/demo only and call out the missing certified provider, official validator/signing, schema, and legal conformance work.
