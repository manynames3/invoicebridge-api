from app.schemas.invoice import NormalizedInvoiceInput
from app.services.country_profiles import get_country_profile
from app.services.validation.base import BaseInvoiceValidator
from app.services.validation.be_peppol import BEPeppolMVPValidator
from app.services.validation.no_network import (
    DEEN16931MVPValidator,
    ESNonVerifactuMVPValidator,
    PLKSeFMVPValidator,
    ROROEFacturaMVPValidator,
)


def get_validator_for_invoice(invoice: NormalizedInvoiceInput) -> BaseInvoiceValidator:
    profile = get_country_profile(invoice.country, invoice.transaction_type)
    if profile and profile.name == "BE_B2B_PEPPOL_MVP":
        return BEPeppolMVPValidator()
    if profile and profile.name == "DE_B2B_EN16931_MVP":
        return DEEN16931MVPValidator()
    if profile and profile.name == "PL_B2B_KSEF_MVP":
        return PLKSeFMVPValidator()
    if profile and profile.name == "RO_B2B_EFACTURA_MVP":
        return ROROEFacturaMVPValidator()
    if profile and profile.name == "ES_B2B_NON_VERIFACTU_MVP":
        return ESNonVerifactuMVPValidator()
    return BEPeppolMVPValidator()
