from app.schemas.invoice import NormalizedInvoiceInput
from app.services.spain_sif import (
    canonical_hash_input,
    qr_payload,
    registration_hash_fields,
    responsible_declaration_draft,
)
from app.services.validation.registry import get_validator_for_invoice


def test_spain_sif_hash_fields_use_official_date_and_amount_formats(spain_invoice: dict) -> None:
    invoice = NormalizedInvoiceInput.model_validate(spain_invoice)
    validation = get_validator_for_invoice(invoice).validate(invoice)

    fields = registration_hash_fields(invoice, validation)
    hash_input = canonical_hash_input(fields)

    assert fields["NIF"] == "A12345674"
    assert fields["FECHAEXPEDICION"] == "05-03-2026"
    assert fields["CUOTATOTAL"] == "105.00"
    assert fields["IMPORTETOTAL"] == "605.00"
    assert "HUELLAANTERIOR=" in hash_input


def test_spain_qr_payload_excludes_record_hash(spain_invoice: dict) -> None:
    invoice = NormalizedInvoiceInput.model_validate(spain_invoice)
    validation = get_validator_for_invoice(invoice).validate(invoice)

    payload = qr_payload(invoice, validation)

    assert "nif=A12345674" in payload
    assert "fecha=05-03-2026" in payload
    assert "importe=605.00" in payload
    assert "hash=" not in payload
    assert "huella=" not in payload


def test_spain_responsible_declaration_draft_is_not_a_certification(spain_invoice: dict) -> None:
    invoice = NormalizedInvoiceInput.model_validate(spain_invoice)

    draft = responsible_declaration_draft(invoice)

    assert draft["status"] == "draft_not_legal_advice"
    assert draft["software"]["verifactu_capable"] is True
    assert "Official AEAT schema/WSDL validation" in draft["external_requirements"]
