# Demo Script

Use this script for a 7-10 minute customer-discovery or hiring-manager demo. Keep the positioning narrow: Germany XRechnung workflow evidence for teams that already produce invoice JSON.

## Setup

Start the API:

```bash
docker-compose up --build
```

In another terminal, run the focused workflow:

```bash
./examples/germany_demo.sh
```

Open the local docs:

```text
http://localhost:8000/docs
```

## Talk Track

1. Start with the pain.

   "Most billing and ERP teams already have invoice data. The expensive part is turning that data into a country-specific structured invoice, proving it passed validation, and keeping evidence when an auditor or customer asks what happened."

2. Position the product.

   "InvoiceBridge API sits behind the existing billing system. The customer sends normalized invoice JSON; the API checks the country profile, validates required fields and totals, generates the structured document, stores evidence, and exposes status and audit trail APIs."

3. Show the readiness check.

   Run:

   ```bash
   curl -s -H "X-API-Key: local-dev-key" \
     "http://localhost:8000/v1/compliance/production-readiness?country=DE&transaction_type=B2B"
   ```

   Say:

   "This is intentionally honest. Germany can work without a paid network provider, but only if the generated XRechnung document passes official validation for the customer payload."

4. Show validation.

   Run:

   ```bash
   curl -s -X POST http://localhost:8000/v1/invoices/validate \
     -H "X-API-Key: local-dev-key" \
     -H "Content-Type: application/json" \
     --data @examples/germany_valid_invoice.json
   ```

   Point out machine-readable validation errors/warnings, totals, country profile, and required format.

5. Show transform and evidence.

   Run:

   ```bash
   curl -s -X POST http://localhost:8000/v1/invoices/transform \
     -H "X-API-Key: local-dev-key" \
     -H "Idempotency-Key: demo-de-001" \
     -H "Content-Type: application/json" \
     --data @examples/germany_valid_invoice.json
   ```

   Say:

   "The response returns an invoice ID, document URL, document SHA-256, and audit event. Idempotency keys prevent accidental duplicate transforms."

6. Show official validation evidence.

   Run:

   ```bash
   curl -s -X POST http://localhost:8000/v1/invoices/{invoice_id}/official-validate \
     -H "X-API-Key: local-dev-key"
   ```

   Say:

   "When a validator command is configured, InvoiceBridge stores the validator result, output, exit code, document hash, and audit event. If it is not configured, the API says that explicitly instead of pretending the document is production-ready."

7. Show status and audit trail.

   Run:

   ```bash
   curl -s -H "X-API-Key: local-dev-key" \
     http://localhost:8000/v1/invoices/status/{invoice_id}

   curl -s -H "X-API-Key: local-dev-key" \
     http://localhost:8000/v1/invoices/{invoice_id}/audit-trail
   ```

   Close with:

   "The sellable workflow is not invoice generation. It is compliance evidence around invoices the customer already creates."

8. Show the trust controls.

   Say:

   "For a pilot, the admin key creates a tenant and returns a tenant API key once. Tenant keys are hashed at rest and can only access their own invoices. If a customer needs cleanup, the archive endpoint redacts the stored payload and XML while preserving evidence hashes."

   Run:

   ```bash
   curl -s -X POST http://localhost:8000/v1/invoices/{invoice_id}/archive \
     -H "X-API-Key: {tenant_api_key}" \
     -H "Content-Type: application/json" \
     -d '{"reason":"customer retention request"}'
   ```

## What Not To Claim

- Do not claim certified Peppol delivery.
- Do not claim government submission for Poland, Romania, Spain, Belgium, or Germany.
- Do not claim legal advice or automatic compliance.
- Do not demo with sensitive production invoice data unless the deployment uses tenant API keys and has agreed retention/privacy terms in place.
