from decimal import Decimal

from app.core.config import get_settings
from app.db.models import Invoice
from app.services.checksum import stable_payload_hash
from app.services.providers.base import BaseEInvoiceProvider, ProviderSubmissionResult


class BaseNoNetworkProvider(BaseEInvoiceProvider):
    reference_prefix: str
    mode: str
    submission_channel = "local_no_network"
    external_government_submission = False

    def submit(
        self,
        invoice: Invoice,
        *,
        simulate_rejection: bool = False,
        simulate_pending: bool = False,
    ) -> ProviderSubmissionResult:
        provider_reference = f"{self.reference_prefix}-{stable_payload_hash(invoice.id)[:12].upper()}"
        normalized_totals = (invoice.validation_result or {}).get("normalized_totals", {})
        payable = Decimal(str(normalized_totals.get("payable_amount", "0")))
        threshold = Decimal(str(get_settings().mock_rejection_threshold))

        if simulate_rejection and payable > threshold:
            return self._result(
                "rejected",
                provider_reference,
                "Simulated local provider rejection for invoice above configured threshold.",
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
                    "mode": self.mode,
                    "external_network_submission": False,
                    "external_government_submission": self.external_government_submission,
                    "submission_channel": self.submission_channel,
                    "legal_compliance": "sandbox_demo_only",
                },
            },
        )


class CustomerManagedDeliveryProvider(BaseNoNetworkProvider):
    network = "CUSTOMER_MANAGED_DELIVERY_MOCK"
    reference_prefix = "LOCAL-DE"
    mode = "customer_managed_delivery"


class LocalFiscalRecordProvider(BaseNoNetworkProvider):
    network = "LOCAL_FISCAL_RECORD_MOCK"
    reference_prefix = "LOCAL-ES-FISCAL"
    mode = "local_fiscal_record_evidence"


class KSeFSandboxProvider(BaseNoNetworkProvider):
    network = "KSEF_GOV_SANDBOX_MOCK"
    reference_prefix = "KSEF-PL-SANDBOX"
    mode = "ksef_government_api_sandbox"
    submission_channel = "direct_government_platform_sandbox"


class ROEFacturaSandboxProvider(BaseNoNetworkProvider):
    network = "RO_EFACTURA_GOV_SANDBOX_MOCK"
    reference_prefix = "ANAF-RO-SANDBOX"
    mode = "ro_efactura_government_api_sandbox"
    submission_channel = "direct_government_platform_sandbox"
