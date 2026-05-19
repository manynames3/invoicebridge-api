from decimal import Decimal
from typing import Any
from urllib.parse import urlencode
from xml.etree import ElementTree as ET

from app.schemas.invoice import NormalizedInvoiceInput
from app.schemas.validation import InvoiceValidationResponse
from app.services.checksum import stable_payload_hash
from app.services.money import money

SFLR_NS = "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroLR.xsd"
SF_NS = "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd"
DS_NS = "http://www.w3.org/2000/09/xmldsig#"
SPANISH_SIF_HASH_ALGORITHM = "SHA-256"
SPANISH_SIF_HASH_SPEC = "BOE-A-2024-22138 Articulo 13.1.a"
SPANISH_SIF_EVENT_HASH_SPEC = "BOE-A-2024-22138 Articulo 13.1.c"
SPANISH_SIF_QR_SPEC = "AEAT QR technical specification; QR excludes the record hash"
SPANISH_SIF_QR_TEST_BASE_URL = "https://prewww2.aeat.es/wlpl/TIKE-CONT/ValidarQRNoVerifactu"
SPANISH_SIF_TEST_VERIFACTU_ENDPOINT = "https://prewww1.aeat.es/wlpl/TIKE-CONT/ws/SistemaFacturacion/VerifactuSOAP"
SPANISH_SIF_TEST_REQUERIMIENTO_ENDPOINT = (
    "https://prewww1.aeat.es/wlpl/TIKE-CONT/ws/SistemaFacturacion/RequerimientoSOAP"
)

ET.register_namespace("sfLR", SFLR_NS)
ET.register_namespace("sf", SF_NS)
ET.register_namespace("ds", DS_NS)


def spanish_nif(value: str | None) -> str:
    if not value:
        return ""
    normalized = value.strip().upper()
    return normalized.removeprefix("ES")


def issue_date_for_qr(invoice: NormalizedInvoiceInput) -> str:
    return invoice.issue_date.strftime("%d-%m-%Y") if invoice.issue_date else ""


def issue_date_for_record(invoice: NormalizedInvoiceInput) -> str:
    return issue_date_for_qr(invoice)


def amount_text(value: Decimal) -> str:
    return f"{money(value):.2f}"


def record_timestamp(invoice: NormalizedInvoiceInput) -> str:
    if invoice.metadata.get("record_timestamp"):
        return str(invoice.metadata["record_timestamp"])
    if invoice.issue_date:
        return f"{invoice.issue_date.isoformat()}T00:00:00+01:00"
    return ""


def previous_record_hash(invoice: NormalizedInvoiceInput) -> str:
    if invoice.metadata.get("first_record") is True:
        return ""
    return str(invoice.metadata.get("previous_record_hash") or "")


def previous_event_hash(invoice: NormalizedInvoiceInput) -> str:
    if invoice.metadata.get("first_event") is True:
        return ""
    return str(invoice.metadata.get("previous_event_hash") or "")


def invoice_type(invoice: NormalizedInvoiceInput) -> str:
    return str(invoice.metadata.get("invoice_type") or "F1").upper()


def previous_record_issue_date(invoice: NormalizedInvoiceInput) -> str:
    value = str(invoice.metadata.get("previous_record_issue_date") or "")
    if len(value) == 10 and value[4] == "-" and value[7] == "-":
        return f"{value[8:10]}-{value[5:7]}-{value[0:4]}"
    return value


def registration_hash_fields(
    invoice: NormalizedInvoiceInput,
    validation: InvoiceValidationResponse,
) -> dict[str, str]:
    totals = validation.normalized_totals
    return {
        "NIF": spanish_nif(getattr(invoice.seller, "vat_id", None)),
        "NUMSERIE": invoice.invoice_number or "",
        "FECHAEXPEDICION": issue_date_for_record(invoice),
        "TIPOFACTURA": invoice_type(invoice),
        "CUOTATOTAL": amount_text(totals.tax_amount),
        "IMPORTETOTAL": amount_text(totals.payable_amount),
        "HUELLAANTERIOR": previous_record_hash(invoice),
        "FECHAHORAHUSOGENREGISTRO": record_timestamp(invoice),
    }


def event_hash_fields(invoice: NormalizedInvoiceInput) -> dict[str, str]:
    return {
        "IDPRODUCTOR": spanish_nif(str(invoice.metadata.get("software_producer_tax_id") or "")),
        "IDSISTEMA": str(invoice.metadata.get("software_system_id") or ""),
        "VERSION": str(invoice.metadata.get("software_version") or ""),
        "NUMEROINSTALACION": str(invoice.metadata.get("installation_number") or ""),
        "HUELLAANTERIOREVENTO": previous_event_hash(invoice),
        "FECHAHORAHUSOGENREGISTRO": record_timestamp(invoice),
    }


def canonical_hash_input(fields: dict[str, str]) -> str:
    return "&".join(f"{key}={value}" for key, value in fields.items())


def registration_record_hash(
    invoice: NormalizedInvoiceInput,
    validation: InvoiceValidationResponse,
) -> str:
    return stable_payload_hash(canonical_hash_input(registration_hash_fields(invoice, validation)))


def event_record_hash(invoice: NormalizedInvoiceInput) -> str:
    return stable_payload_hash(canonical_hash_input(event_hash_fields(invoice)))


def qr_payload(
    invoice: NormalizedInvoiceInput,
    validation: InvoiceValidationResponse,
) -> str:
    query = urlencode(
        {
            "nif": spanish_nif(getattr(invoice.seller, "vat_id", None)),
            "numserie": invoice.invoice_number or "",
            "fecha": issue_date_for_qr(invoice),
            "importe": amount_text(validation.normalized_totals.payable_amount),
        }
    )
    base_url = str(invoice.metadata.get("qr_base_url") or SPANISH_SIF_QR_TEST_BASE_URL)
    return f"{base_url}?{query}"


def build_aeat_registro_alta_xml(
    invoice: NormalizedInvoiceInput,
    validation: InvoiceValidationResponse,
) -> str:
    hash_fields = registration_hash_fields(invoice, validation)
    current_hash = registration_record_hash(invoice, validation)
    root = ET.Element(_name(SFLR_NS, "RegFactuSistemaFacturacion"))

    cabecera = _child(root, SFLR_NS, "Cabecera")
    obligado = _child(cabecera, SF_NS, "ObligadoEmision")
    _child(obligado, SF_NS, "NombreRazon", getattr(invoice.seller, "name", None) or "")
    _child(obligado, SF_NS, "NIF", hash_fields["NIF"])

    registro_factura = _child(root, SFLR_NS, "RegistroFactura")
    alta = _child(registro_factura, SF_NS, "RegistroAlta")
    _child(alta, SF_NS, "IDVersion", "1.0")

    id_factura = _child(alta, SF_NS, "IDFactura")
    _child(id_factura, SF_NS, "IDEmisorFactura", hash_fields["NIF"])
    _child(id_factura, SF_NS, "NumSerieFactura", hash_fields["NUMSERIE"])
    _child(id_factura, SF_NS, "FechaExpedicionFactura", hash_fields["FECHAEXPEDICION"])

    _child(alta, SF_NS, "NombreRazonEmisor", getattr(invoice.seller, "name", None) or "")
    _child(alta, SF_NS, "TipoFactura", invoice_type(invoice))
    _child(alta, SF_NS, "DescripcionOperacion", _operation_description(invoice))
    _destinatarios(alta, invoice)
    _desglose(alta, invoice)
    _child(alta, SF_NS, "CuotaTotal", hash_fields["CUOTATOTAL"])
    _child(alta, SF_NS, "ImporteTotal", hash_fields["IMPORTETOTAL"])
    _encadenamiento(alta, invoice)
    _sistema_informatico(alta, invoice)
    _child(alta, SF_NS, "FechaHoraHusoGenRegistro", hash_fields["FECHAHORAHUSOGENREGISTRO"])
    _child(alta, SF_NS, "TipoHuella", "01")
    _child(alta, SF_NS, "Huella", current_hash)

    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode", xml_declaration=True)


def declaration_summary(invoice: NormalizedInvoiceInput) -> dict[str, Any]:
    metadata = invoice.metadata
    return {
        "producer_tax_id": metadata.get("software_producer_tax_id"),
        "producer_name": metadata.get("software_producer_name"),
        "software_name": metadata.get("software_name"),
        "software_version": metadata.get("software_version"),
        "software_system_id": metadata.get("software_system_id"),
        "installation_number": metadata.get("installation_number"),
        "only_verifactu_capable": bool(metadata.get("only_verifactu_capable", False)),
        "verifactu_capable": metadata.get("verifactu_capable") is True,
        "responsible_declaration_reference": metadata.get("responsible_declaration_reference"),
    }


def responsible_declaration_draft(invoice: NormalizedInvoiceInput) -> dict[str, Any]:
    summary = declaration_summary(invoice)
    return {
        "status": "draft_not_legal_advice",
        "declaration_reference": summary["responsible_declaration_reference"],
        "producer": {
            "tax_id": summary["producer_tax_id"],
            "name": summary["producer_name"],
        },
        "software": {
            "name": summary["software_name"],
            "version": summary["software_version"],
            "system_id": summary["software_system_id"],
            "installation_number": summary["installation_number"],
            "verifactu_capable": summary["verifactu_capable"],
            "only_verifactu_capable": summary["only_verifactu_capable"],
        },
        "statement": (
            "Draft evidence package for a Spanish SIF responsible declaration. The producer must review and issue "
            "the final declaration for the actual product version and deployment."
        ),
        "external_requirements": [
            "Official AEAT schema/WSDL validation",
            "Electronic signing configuration",
            "Immutable local event logging for NO_VERIFACTU operation",
            "AEAT external test portal evidence",
            "VERI*FACTU submission capability",
            "Spanish tax/legal review",
        ],
    }


def tax_breakdown(invoice: NormalizedInvoiceInput) -> list[dict[str, str]]:
    breakdown: dict[Decimal, dict[str, Decimal]] = {}
    for line in invoice.lines:
        quantity = line.quantity or Decimal("0")
        unit_price = line.unit_price or Decimal("0")
        vat_rate = line.vat_rate or Decimal("0")
        line_extension = money(quantity * unit_price)
        line_tax = money(line_extension * vat_rate / Decimal("100"))
        current = breakdown.setdefault(vat_rate, {"taxable": Decimal("0"), "tax": Decimal("0")})
        current["taxable"] = money(current["taxable"] + line_extension)
        current["tax"] = money(current["tax"] + line_tax)
    return [
        {
            "vat_rate": _decimal_text(rate),
            "taxable_amount": amount_text(amounts["taxable"]),
            "tax_amount": amount_text(amounts["tax"]),
        }
        for rate, amounts in sorted(breakdown.items(), key=lambda item: item[0])
    ]


def _name(namespace: str, tag: str) -> str:
    return f"{{{namespace}}}{tag}"


def _child(parent: ET.Element, namespace: str, tag: str, text: str | None = None) -> ET.Element:
    element = ET.SubElement(parent, _name(namespace, tag))
    if text is not None:
        element.text = text
    return element


def _operation_description(invoice: NormalizedInvoiceInput) -> str:
    if invoice.metadata.get("operation_description"):
        return str(invoice.metadata["operation_description"])[:500]
    descriptions = [line.description for line in invoice.lines if line.description]
    return "; ".join(descriptions)[:500] or "Invoice"


def _destinatarios(parent: ET.Element, invoice: NormalizedInvoiceInput) -> None:
    if invoice.buyer is None:
        return
    destinatarios = _child(parent, SF_NS, "Destinatarios")
    destinatario = _child(destinatarios, SF_NS, "IDDestinatario")
    _child(destinatario, SF_NS, "NombreRazon", invoice.buyer.name or "")
    _child(destinatario, SF_NS, "NIF", spanish_nif(invoice.buyer.vat_id))


def _desglose(parent: ET.Element, invoice: NormalizedInvoiceInput) -> None:
    desglose = _child(parent, SF_NS, "Desglose")
    for item in tax_breakdown(invoice):
        detalle = _child(desglose, SF_NS, "DetalleDesglose")
        _child(detalle, SF_NS, "Impuesto", "01")
        _child(detalle, SF_NS, "ClaveRegimen", str(invoice.metadata.get("tax_regime_code") or "01"))
        _child(detalle, SF_NS, "CalificacionOperacion", str(invoice.metadata.get("operation_qualification") or "S1"))
        _child(detalle, SF_NS, "TipoImpositivo", item["vat_rate"])
        _child(detalle, SF_NS, "BaseImponibleOimporteNoSujeto", item["taxable_amount"])
        _child(detalle, SF_NS, "CuotaRepercutida", item["tax_amount"])


def _encadenamiento(parent: ET.Element, invoice: NormalizedInvoiceInput) -> None:
    encadenamiento = _child(parent, SF_NS, "Encadenamiento")
    if invoice.metadata.get("first_record") is True:
        _child(encadenamiento, SF_NS, "PrimerRegistro", "S")
        return
    anterior = _child(encadenamiento, SF_NS, "RegistroAnterior")
    previous_seller_tax_id = str(
        invoice.metadata.get("previous_record_seller_tax_id") or getattr(invoice.seller, "vat_id", "")
    )
    _child(
        anterior,
        SF_NS,
        "IDEmisorFactura",
        spanish_nif(previous_seller_tax_id),
    )
    _child(anterior, SF_NS, "NumSerieFactura", str(invoice.metadata.get("previous_record_invoice_number") or ""))
    _child(anterior, SF_NS, "FechaExpedicionFactura", previous_record_issue_date(invoice))
    _child(anterior, SF_NS, "Huella", previous_record_hash(invoice))


def _sistema_informatico(parent: ET.Element, invoice: NormalizedInvoiceInput) -> None:
    metadata = invoice.metadata
    sistema = _child(parent, SF_NS, "SistemaInformatico")
    _child(sistema, SF_NS, "NombreRazon", str(metadata.get("software_producer_name") or ""))
    _child(sistema, SF_NS, "NIF", spanish_nif(str(metadata.get("software_producer_tax_id") or "")))
    _child(sistema, SF_NS, "NombreSistemaInformatico", str(metadata.get("software_name") or "")[:30])
    _child(sistema, SF_NS, "IdSistemaInformatico", str(metadata.get("software_system_code") or "")[:2])
    _child(sistema, SF_NS, "Version", str(metadata.get("software_version") or ""))
    _child(sistema, SF_NS, "NumeroInstalacion", str(metadata.get("installation_number") or ""))
    _child(sistema, SF_NS, "TipoUsoPosibleSoloVerifactu", "S" if metadata.get("only_verifactu_capable") else "N")
    _child(sistema, SF_NS, "TipoUsoPosibleMultiOT", "S" if metadata.get("multi_taxpayer_capable") else "N")
    _child(sistema, SF_NS, "IndicadorMultiplesOT", "S" if metadata.get("multiple_taxpayers_in_use") else "N")


def _decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f")
