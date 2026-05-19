from app.services.providers.base import BaseEInvoiceProvider
from app.services.providers.mock_peppol import MockPeppolProvider
from app.services.providers.no_network import (
    CustomerManagedDeliveryProvider,
    KSeFMockProvider,
    LocalFiscalRecordProvider,
    ROEFacturaMockProvider,
)


def get_provider_for_network(network: str) -> BaseEInvoiceProvider:
    if network == MockPeppolProvider.network:
        return MockPeppolProvider()
    if network == CustomerManagedDeliveryProvider.network:
        return CustomerManagedDeliveryProvider()
    if network == LocalFiscalRecordProvider.network:
        return LocalFiscalRecordProvider()
    if network == KSeFMockProvider.network:
        return KSeFMockProvider()
    if network == ROEFacturaMockProvider.network:
        return ROEFacturaMockProvider()
    raise ValueError(f"Unsupported provider network: {network}")
