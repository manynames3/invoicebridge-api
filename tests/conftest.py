import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

os.environ["API_KEY"] = "test-key"
os.environ["DATABASE_URL"] = "sqlite:///./test_invoicebridge.db"
os.environ["AUTO_CREATE_TABLES"] = "true"
os.environ["DEPLOYMENT_REGION"] = "test-region-a"
os.environ["REGION_ROLE"] = "primary"
os.environ["DATA_RESIDENCY_REGION"] = "test-residency"
os.environ["ACTIVE_REGIONS"] = "test-region-a,test-region-b"
os.environ["FAILOVER_REGION"] = "test-region-b"

from app.db.models import Base  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def reset_database() -> Generator[None, None, None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"X-API-Key": "test-key"}


@pytest.fixture
def valid_invoice() -> dict:
    return {
        "country": "BE",
        "transaction_type": "B2B",
        "invoice_number": "INV-BE-2026-0001",
        "issue_date": "2026-01-15",
        "currency": "EUR",
        "seller": {
            "name": "Acme Belgium BV",
            "vat_id": "BE0123456789",
            "routing_id": "0208:BE0123456789",
        },
        "buyer": {
            "name": "Globex Belgium NV",
            "vat_id": "BE0987654321",
            "routing_id": "0208:BE0987654321",
        },
        "lines": [
            {
                "line_id": "1",
                "description": "InvoiceBridge API monthly subscription",
                "quantity": "2",
                "unit_price": "100.00",
                "vat_rate": "21",
                "line_extension_amount": "200.00",
                "tax_amount": "42.00",
                "total_amount": "242.00",
            },
            {
                "line_id": "2",
                "description": "Implementation support",
                "quantity": "1",
                "unit_price": "50.00",
                "vat_rate": "6",
                "line_extension_amount": "50.00",
                "tax_amount": "3.00",
                "total_amount": "53.00",
            },
        ],
        "totals": {
            "tax_exclusive_amount": "250.00",
            "tax_amount": "45.00",
            "tax_inclusive_amount": "295.00",
            "payable_amount": "295.00",
        },
        "payment_terms": "Payment due within 30 days",
    }
