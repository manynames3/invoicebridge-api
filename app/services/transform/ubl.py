from decimal import Decimal
from xml.etree import ElementTree as ET

from app.schemas.invoice import InvoiceLine, NormalizedInvoiceInput
from app.schemas.validation import InvoiceValidationResponse
from app.services.checksum import stable_payload_hash
from app.services.money import money
from app.services.transform.base import BaseInvoiceTransformer

CUSTOMIZATION_LABELS = {
    "BE_B2B_PEPPOL_MVP": "InvoiceBridge MVP UBL-like Peppol BIS Billing 3.0 inspired output; not legally compliant",
    "DE_B2B_EN16931_MVP": "InvoiceBridge MVP XRechnung/EN 16931 UBL-like output; not legally compliant",
    "RO_B2B_EFACTURA_MVP": "InvoiceBridge MVP RO_CIUS/UBL 2.1 XML-like output; not legally compliant",
}


class UBLLikeTransformer(BaseInvoiceTransformer):
    """Generate sandbox UBL-like XML for structured invoice profiles."""

    def transform(self, invoice: NormalizedInvoiceInput, validation: InvoiceValidationResponse) -> str:
        root = ET.Element("InvoiceBridgeSandboxInvoice")
        root.set("profile", validation.country_profile_used)
        root.set("format", validation.required_format)
        root.set("legal_compliance", "sandbox_demo_only")

        ET.SubElement(root, "CustomizationID").text = CUSTOMIZATION_LABELS.get(
            validation.country_profile_used,
            "InvoiceBridge MVP UBL-like structured invoice output; not legally compliant",
        )
        ET.SubElement(root, "ProfileID").text = validation.country_profile_used
        ET.SubElement(root, "ID").text = invoice.invoice_number or ""
        ET.SubElement(root, "IssueDate").text = invoice.issue_date.isoformat() if invoice.issue_date else ""
        ET.SubElement(root, "DocumentCurrencyCode").text = invoice.currency or "EUR"

        self._party(root, "AccountingSupplierParty", invoice.seller)
        self._party(root, "AccountingCustomerParty", invoice.buyer)
        self._tax_total(root, validation)
        self._legal_monetary_total(root, validation)
        self._lines(root, invoice.lines)

        ET.indent(root, space="  ")
        return ET.tostring(root, encoding="unicode", xml_declaration=True)

    def _party(self, root: ET.Element, tag: str, party: object) -> None:
        element = ET.SubElement(root, tag)
        party_element = ET.SubElement(element, "Party")
        name = getattr(party, "name", None) or ""
        vat_id = getattr(party, "vat_id", None) or ""
        routing_id = getattr(party, "routing_id", None) or getattr(party, "peppol_id", None) or ""
        ET.SubElement(party_element, "EndpointID", schemeID="INVOICEBRIDGE_SANDBOX").text = routing_id
        ET.SubElement(party_element, "PartyName").text = name
        tax_scheme = ET.SubElement(party_element, "PartyTaxScheme")
        ET.SubElement(tax_scheme, "CompanyID").text = vat_id
        ET.SubElement(tax_scheme, "TaxScheme").text = "VAT"

    def _tax_total(self, root: ET.Element, validation: InvoiceValidationResponse) -> None:
        tax_total = ET.SubElement(root, "TaxTotal")
        ET.SubElement(tax_total, "TaxAmount", currencyID=validation.normalized_totals.currency).text = self._amount(
            validation.normalized_totals.tax_amount
        )

    def _legal_monetary_total(self, root: ET.Element, validation: InvoiceValidationResponse) -> None:
        totals = validation.normalized_totals
        monetary_total = ET.SubElement(root, "LegalMonetaryTotal")
        ET.SubElement(monetary_total, "LineExtensionAmount", currencyID=totals.currency).text = self._amount(
            totals.tax_exclusive_amount
        )
        ET.SubElement(monetary_total, "TaxExclusiveAmount", currencyID=totals.currency).text = self._amount(
            totals.tax_exclusive_amount
        )
        ET.SubElement(monetary_total, "TaxInclusiveAmount", currencyID=totals.currency).text = self._amount(
            totals.tax_inclusive_amount
        )
        ET.SubElement(monetary_total, "PayableAmount", currencyID=totals.currency).text = self._amount(
            totals.payable_amount
        )

    def _lines(self, root: ET.Element, lines: list[InvoiceLine]) -> None:
        for index, line in enumerate(lines, start=1):
            quantity = line.quantity or Decimal("0")
            unit_price = line.unit_price or Decimal("0")
            vat_rate = line.vat_rate or Decimal("0")
            line_extension = money(quantity * unit_price)
            line_element = ET.SubElement(root, "InvoiceLine")
            ET.SubElement(line_element, "ID").text = line.line_id or str(index)
            ET.SubElement(line_element, "InvoicedQuantity").text = str(quantity)
            ET.SubElement(line_element, "LineExtensionAmount").text = self._amount(line_extension)
            item = ET.SubElement(line_element, "Item")
            ET.SubElement(item, "Name").text = line.description or ""
            tax_category = ET.SubElement(item, "ClassifiedTaxCategory")
            ET.SubElement(tax_category, "Percent").text = str(vat_rate)
            price = ET.SubElement(line_element, "Price")
            ET.SubElement(price, "PriceAmount").text = self._amount(unit_price)

    def _amount(self, value: Decimal) -> str:
        return f"{money(value):.2f}"


class FiscalRecordTransformer(BaseInvoiceTransformer):
    """Generate sandbox XML-like fiscal record evidence for Spain NON-VERI*FACTU-style local mode."""

    def transform(self, invoice: NormalizedInvoiceInput, validation: InvoiceValidationResponse) -> str:
        payload = invoice.model_dump(mode="json", exclude_none=True)
        current_hash = stable_payload_hash(
            {
                "profile": validation.country_profile_used,
                "invoice": payload,
                "normalized_totals": validation.normalized_totals.model_dump(mode="json"),
            }
        )

        root = ET.Element("InvoiceBridgeFiscalRecord")
        root.set("profile", validation.country_profile_used)
        root.set("format", validation.required_format)
        root.set("legal_compliance", "sandbox_demo_only")
        ET.SubElement(root, "RecordType").text = "NON_VERIFACTU_LOCAL_FISCAL_RECORD_MVP"
        ET.SubElement(root, "InvoiceNumber").text = invoice.invoice_number or ""
        ET.SubElement(root, "IssueDate").text = invoice.issue_date.isoformat() if invoice.issue_date else ""
        ET.SubElement(root, "Currency").text = invoice.currency or "EUR"
        ET.SubElement(root, "SoftwareSystemID").text = str(invoice.metadata.get("software_system_id", "UNSPECIFIED"))
        ET.SubElement(root, "PreviousRecordHash").text = str(invoice.metadata.get("previous_record_hash", ""))
        ET.SubElement(root, "CurrentRecordHash").text = current_hash
        ET.SubElement(root, "QRCodePayload").text = (
            f"IB-ES|{invoice.invoice_number or ''}|{validation.normalized_totals.payable_amount}|{current_hash[:16]}"
        )

        parties = ET.SubElement(root, "Parties")
        self._party(parties, "Seller", invoice.seller)
        self._party(parties, "Buyer", invoice.buyer)

        totals = validation.normalized_totals
        total_element = ET.SubElement(root, "Totals")
        ET.SubElement(total_element, "TaxExclusiveAmount", currencyID=totals.currency).text = self._amount(
            totals.tax_exclusive_amount
        )
        ET.SubElement(total_element, "TaxAmount", currencyID=totals.currency).text = self._amount(totals.tax_amount)
        ET.SubElement(total_element, "PayableAmount", currencyID=totals.currency).text = self._amount(
            totals.payable_amount
        )

        ET.indent(root, space="  ")
        return ET.tostring(root, encoding="unicode", xml_declaration=True)

    def _party(self, root: ET.Element, tag: str, party: object) -> None:
        element = ET.SubElement(root, tag)
        ET.SubElement(element, "Name").text = getattr(party, "name", None) or ""
        ET.SubElement(element, "TaxID").text = getattr(party, "vat_id", None) or ""

    def _amount(self, value: Decimal) -> str:
        return f"{money(value):.2f}"


class KSeFLikeTransformer(BaseInvoiceTransformer):
    """Generate sandbox XML-like output inspired by Poland KSeF FA(3)."""

    def transform(self, invoice: NormalizedInvoiceInput, validation: InvoiceValidationResponse) -> str:
        root = ET.Element("InvoiceBridgeKSeFInvoice")
        root.set("profile", validation.country_profile_used)
        root.set("format", validation.required_format)
        root.set("legal_compliance", "sandbox_demo_only")
        ET.SubElement(root, "SchemaCode").text = str(invoice.metadata.get("ksef_schema_version", "FA(3)"))
        ET.SubElement(root, "InvoiceNumber").text = invoice.invoice_number or ""
        ET.SubElement(root, "IssueDate").text = invoice.issue_date.isoformat() if invoice.issue_date else ""
        ET.SubElement(root, "Currency").text = invoice.currency or "PLN"

        subject1 = ET.SubElement(root, "Podmiot1")
        self._party(subject1, invoice.seller)
        subject2 = ET.SubElement(root, "Podmiot2")
        self._party(subject2, invoice.buyer)

        totals = validation.normalized_totals
        totals_element = ET.SubElement(root, "Fa")
        ET.SubElement(totals_element, "P_13_1", currencyID=totals.currency).text = self._amount(
            totals.tax_exclusive_amount
        )
        ET.SubElement(totals_element, "P_14_1", currencyID=totals.currency).text = self._amount(totals.tax_amount)
        ET.SubElement(totals_element, "P_15", currencyID=totals.currency).text = self._amount(totals.payable_amount)
        for index, line in enumerate(invoice.lines, start=1):
            self._line(totals_element, index, line)

        ET.indent(root, space="  ")
        return ET.tostring(root, encoding="unicode", xml_declaration=True)

    def _party(self, root: ET.Element, party: object) -> None:
        ET.SubElement(root, "Nazwa").text = getattr(party, "name", None) or ""
        ET.SubElement(root, "NIP").text = (getattr(party, "vat_id", None) or "").removeprefix("PL")

    def _line(self, root: ET.Element, index: int, line: InvoiceLine) -> None:
        quantity = line.quantity or Decimal("0")
        unit_price = line.unit_price or Decimal("0")
        vat_rate = line.vat_rate or Decimal("0")
        line_extension = money(quantity * unit_price)
        line_element = ET.SubElement(root, "FaWiersz")
        ET.SubElement(line_element, "NrWierszaFa").text = line.line_id or str(index)
        ET.SubElement(line_element, "P_7").text = line.description or ""
        ET.SubElement(line_element, "P_8B").text = str(quantity)
        ET.SubElement(line_element, "P_9A").text = self._amount(unit_price)
        ET.SubElement(line_element, "P_11").text = self._amount(line_extension)
        ET.SubElement(line_element, "P_12").text = str(vat_rate)

    def _amount(self, value: Decimal) -> str:
        return f"{money(value):.2f}"
