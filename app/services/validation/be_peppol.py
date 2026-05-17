import re
from decimal import Decimal, InvalidOperation

from app.schemas.invoice import NormalizedInvoiceInput
from app.schemas.validation import InvoiceValidationResponse, NormalizedTotals, ValidationIssue
from app.services.country_profiles import BE_B2B_PEPPOL_MVP
from app.services.money import decimal_text, money, same_money
from app.services.validation.base import BaseInvoiceValidator

VAT_ID_PATTERN = re.compile(r"^BE[0-9]{10}$")


class BEPeppolMVPValidator(BaseInvoiceValidator):
    profile = BE_B2B_PEPPOL_MVP

    def validate(self, invoice: NormalizedInvoiceInput) -> InvoiceValidationResponse:
        errors: list[ValidationIssue] = []
        warnings: list[ValidationIssue] = []

        self._validate_header(invoice, errors)
        self._validate_parties(invoice, errors)
        line_totals = self._validate_lines(invoice, errors, warnings)

        tax_exclusive_amount = money(sum((item[0] for item in line_totals), Decimal("0")))
        tax_amount = money(sum((item[1] for item in line_totals), Decimal("0")))
        tax_inclusive_amount = money(tax_exclusive_amount + tax_amount)
        payable_amount = tax_inclusive_amount

        normalized_totals = NormalizedTotals(
            tax_exclusive_amount=tax_exclusive_amount,
            tax_amount=tax_amount,
            tax_inclusive_amount=tax_inclusive_amount,
            payable_amount=payable_amount,
            currency=invoice.currency or "EUR",
        )

        self._validate_declared_totals(invoice, normalized_totals, errors, warnings)

        return InvoiceValidationResponse(
            compliant=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            normalized_totals=normalized_totals,
            required_format=self.profile.required_format,
            country_profile_used=self.profile.name,
            idempotency_key=invoice.idempotency_key,
            metadata={"delivery_network": self.profile.delivery_network},
        )

    def _validate_header(self, invoice: NormalizedInvoiceInput, errors: list[ValidationIssue]) -> None:
        if (invoice.country or "").upper() != self.profile.country:
            errors.append(
                ValidationIssue(
                    code="UNSUPPORTED_COUNTRY",
                    field="country",
                    message="Only Belgium (BE) is supported by the MVP profile.",
                )
            )
        if (invoice.transaction_type or "").upper() != self.profile.transaction_type:
            errors.append(
                ValidationIssue(
                    code="UNSUPPORTED_TRANSACTION_TYPE",
                    field="transaction_type",
                    message="Only B2B transactions are supported by the Belgium MVP profile.",
                )
            )
        if not invoice.invoice_number:
            errors.append(
                ValidationIssue(
                    code="MISSING_INVOICE_NUMBER",
                    field="invoice_number",
                    message="Invoice number is required.",
                )
            )
        if invoice.issue_date is None:
            errors.append(
                ValidationIssue(code="MISSING_ISSUE_DATE", field="issue_date", message="Issue date is required.")
            )
        if not invoice.currency:
            errors.append(ValidationIssue(code="MISSING_CURRENCY", field="currency", message="Currency is required."))
        elif invoice.currency.upper() not in self.profile.supported_currencies:
            errors.append(
                ValidationIssue(
                    code="UNSUPPORTED_CURRENCY",
                    field="currency",
                    message="The Belgium MVP currently supports EUR invoices only.",
                )
            )

    def _validate_parties(self, invoice: NormalizedInvoiceInput, errors: list[ValidationIssue]) -> None:
        if invoice.seller is None:
            errors.append(ValidationIssue(code="MISSING_SELLER", field="seller", message="Seller is required."))
        else:
            if not invoice.seller.name:
                errors.append(
                    ValidationIssue(code="MISSING_SELLER_NAME", field="seller.name", message="Seller name is required.")
                )
            if not invoice.seller.vat_id:
                errors.append(
                    ValidationIssue(
                        code="MISSING_SELLER_VAT_ID",
                        field="seller.vat_id",
                        message="Seller VAT ID is required for the Belgium MVP profile.",
                    )
                )
            elif not VAT_ID_PATTERN.match(invoice.seller.vat_id):
                errors.append(
                    ValidationIssue(
                        code="INVALID_SELLER_VAT_ID",
                        field="seller.vat_id",
                        message="Seller VAT ID must match the Belgian VAT format BE followed by 10 digits.",
                    )
                )

        if invoice.buyer is None:
            errors.append(ValidationIssue(code="MISSING_BUYER", field="buyer", message="Buyer is required."))
        else:
            if not invoice.buyer.name:
                errors.append(
                    ValidationIssue(code="MISSING_BUYER_NAME", field="buyer.name", message="Buyer name is required.")
                )
            if not invoice.buyer.vat_id:
                errors.append(
                    ValidationIssue(
                        code="MISSING_BUYER_VAT_ID",
                        field="buyer.vat_id",
                        message="Buyer VAT ID is required for the Belgium MVP profile.",
                    )
                )
            elif not VAT_ID_PATTERN.match(invoice.buyer.vat_id):
                errors.append(
                    ValidationIssue(
                        code="INVALID_BUYER_VAT_ID",
                        field="buyer.vat_id",
                        message="Buyer VAT ID must match the Belgian VAT format BE followed by 10 digits.",
                    )
                )
            if not (invoice.buyer.routing_id or invoice.buyer.peppol_id):
                errors.append(
                    ValidationIssue(
                        code="MISSING_BUYER_ROUTING_ID",
                        field="buyer.routing_id",
                        message="Buyer Peppol/routing identifier is required for Belgium B2B MVP delivery.",
                    )
                )

    def _validate_lines(
        self,
        invoice: NormalizedInvoiceInput,
        errors: list[ValidationIssue],
        warnings: list[ValidationIssue],
    ) -> list[tuple[Decimal, Decimal]]:
        if not invoice.lines:
            errors.append(
                ValidationIssue(
                    code="MISSING_INVOICE_LINES",
                    field="lines",
                    message="At least one invoice line is required.",
                )
            )
            return []

        calculated: list[tuple[Decimal, Decimal]] = []
        for index, line in enumerate(invoice.lines):
            field = f"lines[{index}]"
            if not line.description:
                warnings.append(
                    ValidationIssue(
                        code="MISSING_LINE_DESCRIPTION",
                        field=f"{field}.description",
                        message="Line description is recommended for auditability.",
                    )
                )
            quantity = self._required_decimal(line.quantity, f"{field}.quantity", "MISSING_LINE_QUANTITY", errors)
            unit_price = self._required_decimal(
                line.unit_price, f"{field}.unit_price", "MISSING_LINE_UNIT_PRICE", errors
            )
            vat_rate = self._required_decimal(line.vat_rate, f"{field}.vat_rate", "MISSING_LINE_VAT_RATE", errors)
            if quantity is None or unit_price is None or vat_rate is None:
                continue
            if quantity <= 0:
                errors.append(
                    ValidationIssue(
                        code="INVALID_LINE_QUANTITY",
                        field=f"{field}.quantity",
                        message="Line quantity must be greater than zero.",
                    )
                )
            if unit_price < 0:
                errors.append(
                    ValidationIssue(
                        code="INVALID_LINE_UNIT_PRICE",
                        field=f"{field}.unit_price",
                        message="Line unit price must be zero or greater.",
                    )
                )
            if decimal_text(vat_rate) not in self.profile.allowed_vat_rates:
                errors.append(
                    ValidationIssue(
                        code="INVALID_VAT_RATE",
                        field=f"{field}.vat_rate",
                        message="VAT rate must be one of 0, 6, 12, or 21 for the Belgium MVP profile.",
                    )
                )
            line_extension = money(quantity * unit_price)
            line_tax = money(line_extension * vat_rate / Decimal("100"))
            line_total = money(line_extension + line_tax)
            if not same_money(line.line_extension_amount, line_extension):
                errors.append(
                    self._amount_mismatch(
                        "LINE_TOTAL_MISMATCH",
                        f"{field}.line_extension_amount",
                        line.line_extension_amount,
                        line_extension,
                    )
                )
            if not same_money(line.tax_amount, line_tax):
                errors.append(
                    self._amount_mismatch("LINE_TAX_MISMATCH", f"{field}.tax_amount", line.tax_amount, line_tax)
                )
            if not same_money(line.total_amount, line_total):
                errors.append(
                    self._amount_mismatch(
                        "LINE_GROSS_TOTAL_MISMATCH",
                        f"{field}.total_amount",
                        line.total_amount,
                        line_total,
                    )
                )
            calculated.append((line_extension, line_tax))
        return calculated

    def _required_decimal(
        self,
        value: Decimal | None,
        field: str,
        code: str,
        errors: list[ValidationIssue],
    ) -> Decimal | None:
        if value is None:
            errors.append(ValidationIssue(code=code, field=field, message=f"{field} is required."))
            return None
        try:
            return Decimal(value)
        except InvalidOperation:
            errors.append(ValidationIssue(code="INVALID_DECIMAL", field=field, message=f"{field} must be numeric."))
            return None

    def _validate_declared_totals(
        self,
        invoice: NormalizedInvoiceInput,
        normalized: NormalizedTotals,
        errors: list[ValidationIssue],
        warnings: list[ValidationIssue],
    ) -> None:
        if invoice.totals is None:
            errors.append(
                ValidationIssue(
                    code="MISSING_TOTALS",
                    field="totals",
                    message="Invoice totals are required so tax and payable totals can be checked.",
                )
            )
            return

        comparisons = [
            (
                "TOTAL_TAX_EXCLUSIVE_MISMATCH",
                "totals.tax_exclusive_amount",
                invoice.totals.tax_exclusive_amount,
                normalized.tax_exclusive_amount,
            ),
            ("TOTAL_TAX_MISMATCH", "totals.tax_amount", invoice.totals.tax_amount, normalized.tax_amount),
            (
                "TOTAL_TAX_INCLUSIVE_MISMATCH",
                "totals.tax_inclusive_amount",
                invoice.totals.tax_inclusive_amount,
                normalized.tax_inclusive_amount,
            ),
            (
                "TOTAL_PAYABLE_MISMATCH",
                "totals.payable_amount",
                invoice.totals.payable_amount,
                normalized.payable_amount,
            ),
        ]
        for code, field, declared, expected in comparisons:
            if declared is None:
                errors.append(ValidationIssue(code="MISSING_TOTAL", field=field, message=f"{field} is required."))
            elif not same_money(declared, expected):
                errors.append(self._amount_mismatch(code, field, declared, expected))

    def _amount_mismatch(
        self,
        code: str,
        field: str,
        declared: Decimal | None,
        expected: Decimal,
    ) -> ValidationIssue:
        return ValidationIssue(
            code=code,
            field=field,
            message=f"Declared amount {declared} does not match calculated amount {expected}.",
        )


def get_validator() -> BEPeppolMVPValidator:
    return BEPeppolMVPValidator()
