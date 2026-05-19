from app.services.transform.base import BaseInvoiceTransformer
from app.services.transform.ubl import (
    FiscalRecordTransformer,
    KSeFLikeTransformer,
    UBLLikeTransformer,
    XRechnungUBLTransformer,
)


def get_transformer_for_format(required_format: str) -> BaseInvoiceTransformer:
    if required_format in {
        "PEPPOL_BIS_BILLING_3_UBL_LIKE",
        "RO_CIUS_UBL_2_1_XML_LIKE",
    }:
        return UBLLikeTransformer()
    if required_format in {"XRECHNUNG_3_0_UBL", "XRECHNUNG_EN16931_UBL_LIKE"}:
        return XRechnungUBLTransformer()
    if required_format == "KSEF_FA3_XML_LIKE":
        return KSeFLikeTransformer()
    if required_format == "NON_VERIFACTU_FISCAL_RECORD_XML_LIKE":
        return FiscalRecordTransformer()
    raise ValueError(f"Unsupported transform format: {required_format}")
