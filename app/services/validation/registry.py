from app.schemas.invoice import NormalizedInvoiceInput
from app.services.country_profiles import get_country_profile
from app.services.validation.base import BaseInvoiceValidator
from app.services.validation.be_peppol import BEPeppolMVPValidator


def get_validator_for_invoice(invoice: NormalizedInvoiceInput) -> BaseInvoiceValidator:
    profile = get_country_profile(invoice.country, invoice.transaction_type)
    if profile and profile.name == "BE_B2B_PEPPOL_MVP":
        return BEPeppolMVPValidator()
    return BEPeppolMVPValidator()
