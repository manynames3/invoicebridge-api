from abc import ABC, abstractmethod

from app.schemas.invoice import NormalizedInvoiceInput
from app.schemas.validation import InvoiceValidationResponse


class BaseInvoiceTransformer(ABC):
    @abstractmethod
    def transform(self, invoice: NormalizedInvoiceInput, validation: InvoiceValidationResponse) -> str:
        raise NotImplementedError
