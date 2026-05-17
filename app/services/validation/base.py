from abc import ABC, abstractmethod

from app.schemas.invoice import NormalizedInvoiceInput
from app.schemas.validation import InvoiceValidationResponse


class BaseInvoiceValidator(ABC):
    @abstractmethod
    def validate(self, invoice: NormalizedInvoiceInput) -> InvoiceValidationResponse:
        raise NotImplementedError
