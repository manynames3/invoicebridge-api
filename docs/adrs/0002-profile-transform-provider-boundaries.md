# ADR 0002: Keep Country Validation, Transformation, And Providers Separate

## Status

Accepted

## Context

E-invoicing rules vary by country, transaction type, structured format, and delivery network. Combining mandate rules, validation, XML generation, and provider submission would make future countries hard to add.

## Decision

Keep country profiles, validators, transformers, and providers in separate modules with small registries for dispatch.

## Consequences

- Belgium B2B Peppol-style rules are isolated in `BEPeppolMVPValidator`.
- Germany and Spain no-network rules are isolated in `NoNetworkStructuredInvoiceValidator` subclasses.
- Poland KSeF and Romania RO e-Factura sandbox rules are isolated in profile-specific validators.
- UBL-like, KSeF-like, and fiscal-record XML generation are isolated from validation and provider submission.
- Mock Peppol, customer-managed delivery, government-platform sandbox, and local fiscal-record providers are isolated behind `BaseEInvoiceProvider`.
- Adding real KSeF, ANAF/SPV, or Peppol providers should be additive rather than a rewrite.
