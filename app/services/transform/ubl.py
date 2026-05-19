from decimal import Decimal
from xml.etree import ElementTree as ET

from app.schemas.invoice import InvoiceLine, NormalizedInvoiceInput
from app.schemas.validation import InvoiceValidationResponse
from app.services.money import money
from app.services.spain_sif import build_aeat_registro_alta_xml
from app.services.transform.base import BaseInvoiceTransformer

CUSTOMIZATION_LABELS = {
    "BE_B2B_PEPPOL_MVP": "InvoiceBridge MVP UBL-like Peppol BIS Billing 3.0 inspired output; not legally compliant",
    "RO_B2B_EFACTURA_MVP": "InvoiceBridge MVP RO_CIUS/UBL 2.1 XML-like output; not legally compliant",
}
UBL_NS = "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
CAC_NS = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
CBC_NS = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
XRECHNUNG_CUSTOMIZATION_ID = "urn:cen.eu:en16931:2017#compliant#urn:xeinkauf.de:kosit:xrechnung_3.0"
XRECHNUNG_PROFILE_ID = "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0"

ET.register_namespace("", UBL_NS)
ET.register_namespace("cac", CAC_NS)
ET.register_namespace("cbc", CBC_NS)


def xml_name(namespace: str, tag: str) -> str:
    return f"{{{namespace}}}{tag}"


class UBLLikeTransformer(BaseInvoiceTransformer):
    """Generate non-production UBL-like XML for structured invoice profiles."""

    def transform(self, invoice: NormalizedInvoiceInput, validation: InvoiceValidationResponse) -> str:
        root = ET.Element("InvoiceBridgeStructuredInvoice")
        root.set("profile", validation.country_profile_used)
        root.set("format", validation.required_format)
        root.set("legal_compliance", "not_production_ready")

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
        ET.SubElement(party_element, "EndpointID", schemeID="INVOICEBRIDGE_NON_PRODUCTION").text = routing_id
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


class XRechnungUBLTransformer(BaseInvoiceTransformer):
    """Generate UBL 2.1 XML using the XRechnung 3.0 CustomizationID."""

    def transform(self, invoice: NormalizedInvoiceInput, validation: InvoiceValidationResponse) -> str:
        root = ET.Element(xml_name(UBL_NS, "Invoice"))
        self._basic(root, "CustomizationID", XRECHNUNG_CUSTOMIZATION_ID)
        self._basic(root, "ProfileID", XRECHNUNG_PROFILE_ID)
        self._basic(root, "ID", invoice.invoice_number or "")
        self._basic(root, "IssueDate", invoice.issue_date.isoformat() if invoice.issue_date else "")
        if invoice.due_date:
            self._basic(root, "DueDate", invoice.due_date.isoformat())
        self._basic(root, "InvoiceTypeCode", str(invoice.metadata.get("invoice_type_code", "380")))
        self._basic(root, "DocumentCurrencyCode", invoice.currency or validation.normalized_totals.currency)
        self._basic(root, "BuyerReference", self._buyer_reference(invoice))

        self._party(root, "AccountingSupplierParty", invoice.seller)
        self._party(root, "AccountingCustomerParty", invoice.buyer)
        self._delivery(root, invoice)
        self._payment(root, invoice)
        self._tax_total(root, invoice, validation)
        self._legal_monetary_total(root, validation)
        self._lines(root, invoice.lines, validation.normalized_totals.currency)

        ET.indent(root, space="  ")
        return ET.tostring(root, encoding="unicode", xml_declaration=True)

    def _party(self, root: ET.Element, tag: str, party: object) -> None:
        wrapper = self._aggregate(root, tag)
        party_element = self._aggregate(wrapper, "Party")
        vat_id = getattr(party, "vat_id", None) or ""
        name = getattr(party, "name", None) or ""
        self._basic(party_element, "EndpointID", vat_id, schemeID="9930")
        address = self._aggregate(party_element, "PostalAddress")
        party_address = getattr(party, "address", None) or {}
        self._basic(address, "StreetName", str(party_address.get("street", "")))
        self._basic(address, "CityName", str(party_address.get("city", "")))
        self._basic(address, "PostalZone", str(party_address.get("postal_code", "")))
        country = self._aggregate(address, "Country")
        self._basic(country, "IdentificationCode", str(party_address.get("country_code") or "DE"))

        tax_scheme = self._aggregate(party_element, "PartyTaxScheme")
        self._basic(tax_scheme, "CompanyID", vat_id)
        scheme = self._aggregate(tax_scheme, "TaxScheme")
        self._basic(scheme, "ID", "VAT")

        legal_entity = self._aggregate(party_element, "PartyLegalEntity")
        self._basic(legal_entity, "RegistrationName", name)

        contact_name = party_address.get("contact_name")
        phone = party_address.get("phone")
        email = party_address.get("email")
        if contact_name and phone and email:
            contact = self._aggregate(party_element, "Contact")
            self._basic(contact, "Name", str(contact_name or name))
            self._basic(contact, "Telephone", str(phone or ""))
            self._basic(contact, "ElectronicMail", str(email))

    def _delivery(self, root: ET.Element, invoice: NormalizedInvoiceInput) -> None:
        delivery = self._aggregate(root, "Delivery")
        actual_delivery_date = str(invoice.metadata.get("actual_delivery_date") or invoice.issue_date)
        self._basic(delivery, "ActualDeliveryDate", actual_delivery_date)

    def _payment(self, root: ET.Element, invoice: NormalizedInvoiceInput) -> None:
        payment = self._aggregate(root, "PaymentMeans")
        self._basic(payment, "PaymentMeansCode", str(invoice.metadata.get("payment_means_code", "58")))
        iban = invoice.metadata.get("seller_iban")
        if iban:
            account = self._aggregate(payment, "PayeeFinancialAccount")
            self._basic(account, "ID", str(iban))
        if invoice.payment_terms:
            terms = self._aggregate(root, "PaymentTerms")
            self._basic(terms, "Note", invoice.payment_terms)

    def _tax_total(
        self,
        root: ET.Element,
        invoice: NormalizedInvoiceInput,
        validation: InvoiceValidationResponse,
    ) -> None:
        currency = validation.normalized_totals.currency
        total = self._aggregate(root, "TaxTotal")
        self._basic(total, "TaxAmount", self._amount(validation.normalized_totals.tax_amount), currencyID=currency)
        for vat_rate, amounts in self._tax_breakdown(invoice).items():
            subtotal = self._aggregate(total, "TaxSubtotal")
            self._basic(subtotal, "TaxableAmount", self._amount(amounts["taxable"]), currencyID=currency)
            self._basic(subtotal, "TaxAmount", self._amount(amounts["tax"]), currencyID=currency)
            self._tax_category(subtotal, vat_rate)

    def _legal_monetary_total(self, root: ET.Element, validation: InvoiceValidationResponse) -> None:
        totals = validation.normalized_totals
        monetary_total = self._aggregate(root, "LegalMonetaryTotal")
        self._basic(
            monetary_total,
            "LineExtensionAmount",
            self._amount(totals.tax_exclusive_amount),
            currencyID=totals.currency,
        )
        self._basic(
            monetary_total,
            "TaxExclusiveAmount",
            self._amount(totals.tax_exclusive_amount),
            currencyID=totals.currency,
        )
        self._basic(
            monetary_total,
            "TaxInclusiveAmount",
            self._amount(totals.tax_inclusive_amount),
            currencyID=totals.currency,
        )
        self._basic(monetary_total, "PayableAmount", self._amount(totals.payable_amount), currencyID=totals.currency)

    def _lines(self, root: ET.Element, lines: list[InvoiceLine], currency: str) -> None:
        for index, line in enumerate(lines, start=1):
            quantity = line.quantity or Decimal("0")
            unit_price = line.unit_price or Decimal("0")
            vat_rate = line.vat_rate or Decimal("0")
            line_extension = money(quantity * unit_price)

            line_element = self._aggregate(root, "InvoiceLine")
            self._basic(line_element, "ID", line.line_id or str(index))
            self._basic(line_element, "InvoicedQuantity", str(quantity), unitCode=str(line.unit_code or "C62"))
            self._basic(line_element, "LineExtensionAmount", self._amount(line_extension), currencyID=currency)
            item = self._aggregate(line_element, "Item")
            self._basic(item, "Name", line.description or "")
            self._tax_category(item, vat_rate, tag="ClassifiedTaxCategory")
            price = self._aggregate(line_element, "Price")
            self._basic(price, "PriceAmount", self._amount(unit_price), currencyID=currency)

    def _tax_category(self, root: ET.Element, vat_rate: Decimal, *, tag: str = "TaxCategory") -> None:
        category = self._aggregate(root, tag)
        self._basic(category, "ID", "Z" if vat_rate == Decimal("0") else "S")
        self._basic(category, "Percent", self._decimal_text(vat_rate))
        scheme = self._aggregate(category, "TaxScheme")
        self._basic(scheme, "ID", "VAT")

    def _tax_breakdown(self, invoice: NormalizedInvoiceInput) -> dict[Decimal, dict[str, Decimal]]:
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
        return breakdown

    def _buyer_reference(self, invoice: NormalizedInvoiceInput) -> str:
        return str(
            invoice.metadata.get("buyer_reference")
            or getattr(invoice.buyer, "routing_id", None)
            or getattr(invoice.buyer, "vat_id", None)
            or "UNKNOWN"
        )

    def _aggregate(self, root: ET.Element, tag: str) -> ET.Element:
        return ET.SubElement(root, xml_name(CAC_NS, tag))

    def _basic(self, root: ET.Element, tag: str, text: str, **attributes: str) -> ET.Element:
        element = ET.SubElement(root, xml_name(CBC_NS, tag), attributes)
        element.text = text
        return element

    def _amount(self, value: Decimal) -> str:
        return f"{money(value):.2f}"

    def _decimal_text(self, value: Decimal) -> str:
        return format(value.normalize(), "f")


class FiscalRecordTransformer(BaseInvoiceTransformer):
    """Generate AEAT SIF RegistroAlta XML for Spain."""

    def transform(self, invoice: NormalizedInvoiceInput, validation: InvoiceValidationResponse) -> str:
        return build_aeat_registro_alta_xml(invoice, validation)


class KSeFLikeTransformer(BaseInvoiceTransformer):
    """Generate non-production XML-like output inspired by Poland KSeF FA(3)."""

    def transform(self, invoice: NormalizedInvoiceInput, validation: InvoiceValidationResponse) -> str:
        root = ET.Element("InvoiceBridgeKSeFInvoice")
        root.set("profile", validation.country_profile_used)
        root.set("format", validation.required_format)
        root.set("legal_compliance", "not_production_ready")
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
