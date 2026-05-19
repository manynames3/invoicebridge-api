from decimal import Decimal

from app.core.config import get_settings
from app.db.models import Invoice
from app.services.checksum import stable_payload_hash
from app.services.providers.base import BaseEInvoiceProvider, ProviderSubmissionResult


class MockPeppolProvider(BaseEInvoiceProvider):
    network = "PEPPOL_MOCK"

    def submit(
        self,
        invoice: Invoice,
        *,
        simulate_rejection: bool = False,
        simulate_pending: bool = False,
    ) -> ProviderSubmissionResult:
        provider_reference = f"MOCK-PEPPOL-{stable_payload_hash(invoice.id)[:12].upper()}"

        if not invoice.buyer_routing_id:
            return self._result(
                "rejected",
                provider_reference,
                "Buyer Peppol/routing identifier is missing.",
                {"rule": "buyer_routing_id_required"},
            )

        normalized_totals = (invoice.validation_result or {}).get("normalized_totals", {})
        payable = Decimal(str(normalized_totals.get("payable_amount", "0")))
        threshold = Decimal(str(get_settings().mock_rejection_threshold))
        if simulate_rejection and payable > threshold:
            return self._result(
                "rejected",
                provider_reference,
                "Simulated provider rejection for invoice above configured threshold.",
                {"rule": "simulate_rejection_threshold", "threshold": str(threshold)},
            )

        if simulate_pending or invoice.invoice_number.upper().endswith("-PENDING"):
            return self._result("pending", provider_reference, None, {"rule": "deterministic_pending"})

        return self._result("accepted", provider_reference, None, {"rule": "valid_invoice_default_accept"})

    def _result(
        self,
        status: str,
        provider_reference: str,
        rejection_reason: str | None,
        metadata: dict,
    ) -> ProviderSubmissionResult:
        return ProviderSubmissionResult(
            network=self.network,
            delivery_status=status,
            provider_reference=provider_reference,
            rejection_reason=rejection_reason,
            response_payload={
                "network": self.network,
                "delivery_status": status,
                "provider_reference": provider_reference,
                "rejection_reason": rejection_reason,
                "metadata": {
                    **metadata,
                    "mode": "mock_peppol_access_point",
                    "external_network_submission": False,
                    "submission_channel": "peppol_mock",
                    "legal_compliance": "not_production_ready",
                },
            },
        )
