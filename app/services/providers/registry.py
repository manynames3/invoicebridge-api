from app.services.providers.base import BaseEInvoiceProvider
from app.services.providers.mock_peppol import MockPeppolProvider


def get_provider_for_network(network: str) -> BaseEInvoiceProvider:
    if network == MockPeppolProvider.network:
        return MockPeppolProvider()
    raise ValueError(f"Unsupported provider network: {network}")
