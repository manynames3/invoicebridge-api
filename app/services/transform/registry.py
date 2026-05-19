from app.services.transform.base import BaseInvoiceTransformer
from app.services.transform.ubl import FiscalRecordTransformer, UBLLikeTransformer


def get_transformer_for_format(required_format: str) -> BaseInvoiceTransformer:
    if required_format in {"PEPPOL_BIS_BILLING_3_UBL_LIKE", "XRECHNUNG_EN16931_UBL_LIKE"}:
        return UBLLikeTransformer()
    if required_format == "NON_VERIFACTU_FISCAL_RECORD_XML_LIKE":
        return FiscalRecordTransformer()
    raise ValueError(f"Unsupported transform format: {required_format}")
