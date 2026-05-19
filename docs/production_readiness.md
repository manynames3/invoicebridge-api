# Production Readiness Without Paid Network Providers

InvoiceBridge can support no-paid-provider paths, but that is not the same as no compliance work. A customer can only rely on the system for a legal mandate after official validation, credentials, signing, and country-specific operational evidence are configured.

## What The API Enforces

- `/v1/compliance/production-readiness` returns explicit blockers for each country profile.
- `/v1/invoices/{invoice_id}/official-validate` runs the configured country validator command against the stored XML artifact.
- Transform responses include `document_url` and `document_sha256` so customers can retrieve and verify generated artifacts.
- Provider responses include metadata that identifies whether the flow was mock, local, direct-government sandbox, or externally submitted.

## Country Paths

| Country | No-paid-provider path | Must be configured before production reliance |
|---|---|---|
| Germany | Customer-managed structured e-invoice exchange | Passing official XRechnung/EN16931 validation, such as a KoSIT validator command |
| Poland | Direct KSeF government API | FA(3) schema validation, KSeF API URL, encryption/authentication, customer KSeF credentials/certificates, UPO handling |
| Romania | Direct ANAF/SPV API | RO_CIUS validation, ANAF API URL, SPV/OAuth credentials, upload/status polling, signed response handling |
| Spain | Local SIF/non-VERI*FACTU-style record controls with software identity and SHA-256 hash chaining | Official SIF record validation, record signing, QR/hash/event-log requirements, responsible declaration readiness |

## Configuration

```env
XRECHNUNG_VALIDATOR_COMMAND=
KSEF_SCHEMA_VALIDATOR_COMMAND=
KSEF_API_BASE_URL=
KSEF_CREDENTIALS_CONFIGURED=false
RO_EFACTURA_SCHEMA_VALIDATOR_COMMAND=
RO_EFACTURA_API_BASE_URL=
RO_EFACTURA_OAUTH_CONFIGURED=false
SPANISH_SIF_VALIDATOR_COMMAND=
SPANISH_SIF_SIGNING_CONFIGURED=false
SPANISH_SIF_RESPONSIBLE_DECLARATION_READY=false
```

Validator commands receive the XML path as the final argument unless the command contains a `{xml}` placeholder.

Install the free KoSIT/XRechnung validator artifacts:

```bash
make setup-xrechnung-validator
export XRECHNUNG_VALIDATOR_COMMAND="vendor/xrechnung/validate-xrechnung.sh {xml}"
```

The Docker image installs Java plus the KoSIT validator/configuration artifacts and sets `XRECHNUNG_VALIDATOR_COMMAND` automatically.

The bundled Germany example invoice was checked locally against KoSIT Validator `1.6.0` with XRechnung validator configuration `3.0.2` and was accepted. Customer payloads must still be validated invoice by invoice.

## Production Boundary

The repository does not ship customer credentials, government enrollment, legal review, certificate material, or official country conformance packs. Those are customer/deployment responsibilities. The API is designed to make those dependencies explicit and testable instead of hiding them behind mock success responses.
