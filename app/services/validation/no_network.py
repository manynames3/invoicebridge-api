import re
from decimal import Decimal, InvalidOperation
from typing import Protocol

from app.schemas.invoice import NormalizedInvoiceInput
from app.schemas.validation import InvoiceValidationResponse, NormalizedTotals, ValidationIssue
from app.services.country_profiles import (
    DE_B2B_EN16931_MVP,
    ES_B2B_NON_VERIFACTU_MVP,
    PL_B2B_KSEF_MVP,
    RO_B2B_EFACTURA_MVP,
    CountryProfileDefinition,
)
from app.services.money import decimal_text, money, same_money
from app.services.validation.base import BaseInvoiceValidator

DE_VAT_ID_PATTERN = re.compile(r"^DE[0-9]{9}$")
PL_NIP_PATTERN = re.compile(r"^PL[0-9]{10}$")
RO_VAT_ID_PATTERN = re.compile(r"^RO[0-9]{2,10}$")
ES_VAT_ID_PATTERN = re.compile(r"^ES[A-Z0-9][A-Z0-9]{7}[A-Z0-9]$")
SPANISH_NIF_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"
SPANISH_CIF_CONTROL_LETTERS = "JABCDEFGHI"


class VatIdCheck(Protocol):
    def __call__(self, vat_id: str) -> bool:
        ...


class NoNetworkStructuredInvoiceValidator(BaseInvoiceValidator):
    def __init__(
        self,
        *,
        profile: CountryProfileDefinition,
        country_name: str,
        vat_id_pattern: re.Pattern[str],
        vat_id_name: str,
        vat_id_check: VatIdCheck | None = None,
        vat_id_check_message: str | None = None,
    ) -> None:
        self.profile = profile
        self.country_name = country_name
        self.vat_id_pattern = vat_id_pattern
        self.vat_id_name = vat_id_name
        self.vat_id_check = vat_id_check
        self.vat_id_check_message = vat_id_check_message

    def validate(self, invoice: NormalizedInvoiceInput) -> InvoiceValidationResponse:
        errors: list[ValidationIssue] = []
        warnings: list[ValidationIssue] = []

        self._validate_header(invoice, errors)
        self._validate_parties(invoice, errors)
        self._validate_profile_specific_metadata(invoice, warnings)
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

        self._validate_declared_totals(invoice, normalized_totals, errors)

        return InvoiceValidationResponse(
            compliant=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            normalized_totals=normalized_totals,
            required_format=self.profile.required_format,
            country_profile_used=self.profile.name,
            idempotency_key=invoice.idempotency_key,
            metadata={
                "delivery_network": self.profile.delivery_network,
                "delivery_model": self._delivery_model(),
            },
        )

    def _delivery_model(self) -> str:
        if self.profile.name == ES_B2B_NON_VERIFACTU_MVP.name:
            return "local_fiscal_record_no_network"
        if self.profile.name in {PL_B2B_KSEF_MVP.name, RO_B2B_EFACTURA_MVP.name}:
            return "direct_government_platform_sandbox"
        return "customer_managed_no_network"

    def _validate_header(self, invoice: NormalizedInvoiceInput, errors: list[ValidationIssue]) -> None:
        if (invoice.country or "").upper() != self.profile.country:
            errors.append(
                ValidationIssue(
                    code="UNSUPPORTED_COUNTRY",
                    field="country",
                    message=f"Only {self.country_name} ({self.profile.country}) is supported by this profile.",
                )
            )
        if (invoice.transaction_type or "").upper() != self.profile.transaction_type:
            errors.append(
                ValidationIssue(
                    code="UNSUPPORTED_TRANSACTION_TYPE",
                    field="transaction_type",
                    message=f"Only B2B transactions are supported by the {self.country_name} MVP profile.",
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
                ValidationIssue(
                    code="MISSING_ISSUE_DATE",
                    field="issue_date",
                    message="Issue date is required.",
                )
            )
        if not invoice.currency:
            errors.append(ValidationIssue(code="MISSING_CURRENCY", field="currency", message="Currency is required."))
        elif invoice.currency.upper() not in self.profile.supported_currencies:
            currencies = ", ".join(sorted(self.profile.supported_currencies))
            errors.append(
                ValidationIssue(
                    code="UNSUPPORTED_CURRENCY",
                    field="currency",
                    message=f"The {self.country_name} MVP currently supports {currencies} invoices.",
                )
            )

    def _validate_parties(self, invoice: NormalizedInvoiceInput, errors: list[ValidationIssue]) -> None:
        self._validate_party(invoice.seller, "seller", errors)
        self._validate_party(invoice.buyer, "buyer", errors)

    def _validate_party(self, party: object, party_name: str, errors: list[ValidationIssue]) -> None:
        label = party_name.capitalize()
        if party is None:
            errors.append(
                ValidationIssue(code=f"MISSING_{party_name.upper()}", field=party_name, message=f"{label} is required.")
            )
            return

        name = getattr(party, "name", None)
        vat_id = getattr(party, "vat_id", None)
        if not name:
            errors.append(
                ValidationIssue(
                    code=f"MISSING_{party_name.upper()}_NAME",
                    field=f"{party_name}.name",
                    message=f"{label} name is required.",
                )
            )
        if not vat_id:
            errors.append(
                ValidationIssue(
                    code=f"MISSING_{party_name.upper()}_VAT_ID",
                    field=f"{party_name}.vat_id",
                    message=f"{label} VAT/tax ID is required for the {self.country_name} MVP profile.",
                )
            )
        elif not self.vat_id_pattern.match(vat_id):
            errors.append(
                ValidationIssue(
                    code=f"INVALID_{party_name.upper()}_VAT_ID",
                    field=f"{party_name}.vat_id",
                    message=f"{label} VAT/tax ID must match the {self.vat_id_name} format.",
                )
            )
        elif self.vat_id_check and not self.vat_id_check(vat_id):
            errors.append(
                ValidationIssue(
                    code=f"INVALID_{party_name.upper()}_VAT_ID_CHECKSUM",
                    field=f"{party_name}.vat_id",
                    message=self.vat_id_check_message or f"{label} VAT/tax ID failed checksum validation.",
                )
            )

    def _validate_profile_specific_metadata(
        self,
        invoice: NormalizedInvoiceInput,
        warnings: list[ValidationIssue],
    ) -> None:
        if self.profile.name != ES_B2B_NON_VERIFACTU_MVP.name:
            if self.profile.name == PL_B2B_KSEF_MVP.name and not invoice.metadata.get("ksef_schema_version"):
                warnings.append(
                    ValidationIssue(
                        code="MISSING_KSEF_SCHEMA_VERSION",
                        field="metadata.ksef_schema_version",
                        message="Poland KSeF sandbox profiles should identify the target FA schema version.",
                    )
                )
            if self.profile.name == RO_B2B_EFACTURA_MVP.name and not invoice.metadata.get("anaf_submission_context"):
                warnings.append(
                    ValidationIssue(
                        code="MISSING_ANAF_SUBMISSION_CONTEXT",
                        field="metadata.anaf_submission_context",
                        message="Romania RO e-Factura production submission requires ANAF/SPV authorization context.",
                    )
                )
            return
        if not invoice.metadata.get("software_system_id"):
            warnings.append(
                ValidationIssue(
                    code="MISSING_SOFTWARE_SYSTEM_ID",
                    field="metadata.software_system_id",
                    message="Spain fiscal-record profiles should identify the invoicing software system.",
                )
            )
        if not invoice.metadata.get("previous_record_hash"):
            warnings.append(
                ValidationIssue(
                    code="MISSING_PREVIOUS_RECORD_HASH",
                    field="metadata.previous_record_hash",
                    message="Previous record hash is recommended for chained local fiscal record evidence.",
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
                allowed = ", ".join(sorted(self.profile.allowed_vat_rates, key=Decimal))
                errors.append(
                    ValidationIssue(
                        code="INVALID_VAT_RATE",
                        field=f"{field}.vat_rate",
                        message=f"VAT rate must be one of {allowed} for the {self.country_name} MVP profile.",
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


def polish_nip_checksum(vat_id: str) -> bool:
    digits = vat_id.removeprefix("PL")
    if len(digits) != 10 or not digits.isdigit():
        return False
    weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]
    checksum = sum(int(digit) * weight for digit, weight in zip(digits[:9], weights, strict=True)) % 11
    return checksum != 10 and checksum == int(digits[9])


def german_vat_checksum(vat_id: str) -> bool:
    digits = vat_id.removeprefix("DE")
    if len(digits) != 9 or not digits.isdigit():
        return False

    product = 10
    for digit in digits[:8]:
        total = (int(digit) + product) % 10
        if total == 0:
            total = 10
        product = (2 * total) % 11

    checksum = 11 - product
    if checksum == 10:
        checksum = 0
    return checksum == int(digits[8])


def romanian_cui_checksum(vat_id: str) -> bool:
    digits = vat_id.removeprefix("RO")
    if not 2 <= len(digits) <= 10 or not digits.isdigit():
        return False

    control_digit = int(digits[-1])
    payload = digits[:-1]
    weights = [7, 5, 3, 2, 1, 7, 5, 3, 2]
    total = sum(int(digit) * weights[index] for index, digit in enumerate(reversed(payload)))
    checksum = (total * 10) % 11
    if checksum == 10:
        checksum = 0
    return checksum == control_digit


def spanish_tax_id_checksum(vat_id: str) -> bool:
    identifier = vat_id.removeprefix("ES").upper()
    if re.match(r"^[0-9]{8}[A-Z]$", identifier):
        return _spanish_nif_checksum(identifier[:8], identifier[8])
    if re.match(r"^[XYZ][0-9]{7}[A-Z]$", identifier):
        numeric_prefix = {"X": "0", "Y": "1", "Z": "2"}[identifier[0]]
        return _spanish_nif_checksum(numeric_prefix + identifier[1:8], identifier[8])
    if re.match(r"^[ABCDEFGHJNPQRSUVW][0-9]{7}[0-9A-J]$", identifier):
        return _spanish_cif_checksum(identifier)
    return False


def _spanish_nif_checksum(digits: str, control_letter: str) -> bool:
    return SPANISH_NIF_LETTERS[int(digits) % 23] == control_letter


def _spanish_cif_checksum(identifier: str) -> bool:
    digits = identifier[1:8]
    control = identifier[8]
    total = 0
    for index, digit_text in enumerate(digits, start=1):
        digit = int(digit_text)
        if index % 2:
            doubled = digit * 2
            total += doubled // 10 + doubled % 10
        else:
            total += digit
    control_digit = (10 - (total % 10)) % 10
    return control == str(control_digit) or control == SPANISH_CIF_CONTROL_LETTERS[control_digit]


class DEEN16931MVPValidator(NoNetworkStructuredInvoiceValidator):
    def __init__(self) -> None:
        super().__init__(
            profile=DE_B2B_EN16931_MVP,
            country_name="Germany",
            vat_id_pattern=DE_VAT_ID_PATTERN,
            vat_id_name="German VAT ID format DE followed by 9 digits",
            vat_id_check=german_vat_checksum,
            vat_id_check_message="German VAT ID failed checksum validation.",
        )


class PLKSeFMVPValidator(NoNetworkStructuredInvoiceValidator):
    def __init__(self) -> None:
        super().__init__(
            profile=PL_B2B_KSEF_MVP,
            country_name="Poland",
            vat_id_pattern=PL_NIP_PATTERN,
            vat_id_name="Polish NIP format PL followed by 10 digits",
            vat_id_check=polish_nip_checksum,
            vat_id_check_message="Polish NIP failed checksum validation.",
        )


class ROROEFacturaMVPValidator(NoNetworkStructuredInvoiceValidator):
    def __init__(self) -> None:
        super().__init__(
            profile=RO_B2B_EFACTURA_MVP,
            country_name="Romania",
            vat_id_pattern=RO_VAT_ID_PATTERN,
            vat_id_name="Romanian VAT/CUI format RO followed by 2 to 10 digits",
            vat_id_check=romanian_cui_checksum,
            vat_id_check_message="Romanian VAT/CUI failed checksum validation.",
        )


class ESNonVerifactuMVPValidator(NoNetworkStructuredInvoiceValidator):
    def __init__(self) -> None:
        super().__init__(
            profile=ES_B2B_NON_VERIFACTU_MVP,
            country_name="Spain",
            vat_id_pattern=ES_VAT_ID_PATTERN,
            vat_id_name="Spanish VAT/NIF format ES followed by 9 alphanumeric characters",
            vat_id_check=spanish_tax_id_checksum,
            vat_id_check_message="Spanish VAT/NIF/CIF failed checksum validation.",
        )
