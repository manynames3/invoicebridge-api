# Spain SIF / VERI*FACTU Readiness

Spain is not ready for legal production use in this repository. AEAT does not pre-certify the software through this repository; production use still requires official technical validation, signing, test-portal evidence, customer-specific deployment controls, and a responsible declaration.

## What Is Implemented

- Spanish VAT/NIF/CIF checksum validation.
- Required SIF metadata: invoice type, producer identity, software identity, installation number, timestamp, VERI*FACTU capability, event-log flag, and previous record/event hashes.
- AEAT `RegFactuSistemaFacturacion` XML output containing a `RegistroAlta` record with official WSDL/XSD namespaces.
- Official hash input fields named in Orden HAC/1177/2024 article 13.1.a.
- SHA-256 record hash for invoice registration records.
- SHA-256 event hash using producer/system/version/installation fields named in article 13.1.c.
- QR payload draft with issuer NIF, invoice number, issue date, and total amount. The record hash is not included in the QR payload.
- `sif_record_generated` audit event containing record hash, event hash, and responsible-declaration metadata.
- Optional `SPANISH_SIF_SIGNING_COMMAND` interface for deployment-specific XML signing.
- Responsible declaration draft endpoint: `/v1/invoices/{invoice_id}/spain/responsible-declaration`.
- AEAT WSDL/XSD asset setup script: `make setup-spanish-sif-assets`.
- Production-readiness blockers for validator command, signing, immutable event log, AEAT external test evidence, VERI*FACTU submission capability, and responsible declaration readiness.

## Local Official Schema Check

Install AEAT WSDL/XSD assets and configure the local validator:

```bash
make setup-spanish-sif-assets
export SPANISH_SIF_VALIDATOR_COMMAND="vendor/spanish-sif/validate-spanish-sif.sh {xml}"
```

Then transform a Spain invoice and run:

```bash
curl -s -X POST http://localhost:8000/v1/invoices/{invoice_id}/official-validate \
  -H "X-API-Key: local-dev-key"
```

The bundled `examples/spain_valid_invoice.json` sample has been checked locally against the downloaded AEAT `SuministroLR.xsd` schema with `xmllint`.

## What Still Blocks Production Reliance

- Official AEAT validation must be configured and passing for each generated document.
- NO_VERI*FACTU deployments require compliant electronic signing and immutable local event logging.
- The product must remain capable of VERI*FACTU submission even when a customer chooses NO_VERI*FACTU operation.
- The responsible declaration must be prepared for the actual software producer, software version, deployment model, and customer use case.
- The flow must be tested against the AEAT external test portal.
- Spanish tax/legal review is required before marketing or operating this as compliant software.

## Official References

- AEAT SIF / VERI*FACTU portal: https://sede.agenciatributaria.gob.es/Sede/iva/sistemas-informaticos-facturacion-verifactu.html
- AEAT technical information: https://sede.agenciatributaria.gob.es/Sede/iva/sistemas-informaticos-facturacion-verifactu/informacion-tecnica.html
- AEAT hash FAQ: https://sede.agenciatributaria.gob.es/Sede/iva/sistemas-informaticos-facturacion-verifactu/preguntas-frecuentes/huella-hash.html
- AEAT responsible declaration FAQ: https://sede.agenciatributaria.gob.es/Sede/iva/sistemas-informaticos-facturacion-verifactu/preguntas-frecuentes/certificacion-sistemas-informaticos-declaracion-responsable.html
- Orden HAC/1177/2024: https://www.boe.es/buscar/act.php?id=BOE-A-2024-22138
