# ADR 0002: Keep Country Validation, Transformation, And Providers Separate

## Status

Accepted

## Context

E-invoicing rules vary by country, transaction type, structured format, and delivery network. Combining mandate rules, validation, XML generation, and provider submission would make future countries hard to add.

## Decision

Keep country profiles, validators, transformers, and providers in separate modules with small registries for dispatch.

## Consequences

- Belgium B2B Peppol-style rules are isolated in `BEPeppolMVPValidator`.
- UBL-like XML generation is isolated from validation and provider submission.
- Mock Peppol submission is isolated behind `BaseEInvoiceProvider`.
- Adding KSeF or a real Peppol provider should be additive rather than a rewrite.
