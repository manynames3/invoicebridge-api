from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.db.models import Invoice


@dataclass(frozen=True)
class ProviderSubmissionResult:
    network: str
    delivery_status: str
    provider_reference: str
    rejection_reason: str | None
    response_payload: dict


class BaseEInvoiceProvider(ABC):
    network: str

    @abstractmethod
    def submit(
        self,
        invoice: Invoice,
        *,
        simulate_rejection: bool = False,
        simulate_pending: bool = False,
    ) -> ProviderSubmissionResult:
        raise NotImplementedError
