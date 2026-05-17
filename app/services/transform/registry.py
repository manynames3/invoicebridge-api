from app.services.transform.base import BaseInvoiceTransformer
from app.services.transform.ubl import UBLLikeTransformer


def get_transformer_for_format(required_format: str) -> BaseInvoiceTransformer:
    if required_format == "PEPPOL_BIS_BILLING_3_UBL_LIKE":
        return UBLLikeTransformer()
    raise ValueError(f"Unsupported transform format: {required_format}")
