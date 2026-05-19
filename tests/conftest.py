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
os.environ["XRECHNUNG_VALIDATOR_COMMAND"] = ""

from app.core.config import get_settings  # noqa: E402
from app.db.models import Base  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def reset_database() -> Generator[None, None, None]:
    get_settings.cache_clear()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    get_settings.cache_clear()
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


@pytest.fixture
def germany_invoice() -> dict:
    return {
        "country": "DE",
        "transaction_type": "B2B",
        "invoice_number": "INV-DE-2026-0001",
        "issue_date": "2026-02-10",
        "due_date": "2026-03-12",
        "currency": "EUR",
        "seller": {
            "name": "Acme Deutschland GmbH",
            "vat_id": "DE123456788",
            "country_code": "DE",
            "address": {
                "street": "Friedrichstrasse 100",
                "city": "Berlin",
                "postal_code": "10117",
                "country_code": "DE",
                "contact_name": "Billing Team",
                "phone": "+49301234567",
                "email": "billing@example.de",
            },
        },
        "buyer": {
            "name": "Globex Deutschland GmbH",
            "vat_id": "DE987654328",
            "country_code": "DE",
            "address": {
                "street": "Kaufingerstrasse 12",
                "city": "Munich",
                "postal_code": "80331",
                "country_code": "DE",
                "email": "ap@example.de",
            },
        },
        "lines": [
            {
                "line_id": "1",
                "description": "Compliance API monthly subscription",
                "quantity": "3",
                "unit_price": "100.00",
                "vat_rate": "19",
                "line_extension_amount": "300.00",
                "tax_amount": "57.00",
                "total_amount": "357.00",
            }
        ],
        "totals": {
            "tax_exclusive_amount": "300.00",
            "tax_amount": "57.00",
            "tax_inclusive_amount": "357.00",
            "payable_amount": "357.00",
        },
        "payment_terms": "Payment due within 30 days",
        "metadata": {
            "buyer_reference": "DE-BUYER-REF-2026-0001",
            "seller_iban": "DE89370400440532013000",
            "payment_means_code": "58",
        },
    }


@pytest.fixture
def poland_invoice() -> dict:
    return {
        "country": "PL",
        "transaction_type": "B2B",
        "invoice_number": "INV-PL-2026-0001",
        "issue_date": "2026-04-15",
        "currency": "PLN",
        "seller": {
            "name": "Acme Polska Sp. z o.o.",
            "vat_id": "PL5250007738",
            "country_code": "PL",
        },
        "buyer": {
            "name": "Globex Polska Sp. z o.o.",
            "vat_id": "PL5260250274",
            "country_code": "PL",
        },
        "lines": [
            {
                "line_id": "1",
                "description": "KSeF evaluation workflow",
                "quantity": "2",
                "unit_price": "1000.00",
                "vat_rate": "23",
                "line_extension_amount": "2000.00",
                "tax_amount": "460.00",
                "total_amount": "2460.00",
            }
        ],
        "totals": {
            "tax_exclusive_amount": "2000.00",
            "tax_amount": "460.00",
            "tax_inclusive_amount": "2460.00",
            "payable_amount": "2460.00",
        },
        "payment_terms": "Payment due within 14 days",
        "metadata": {"ksef_schema_version": "FA(3)"},
    }


@pytest.fixture
def romania_invoice() -> dict:
    return {
        "country": "RO",
        "transaction_type": "B2B",
        "invoice_number": "INV-RO-2026-0001",
        "issue_date": "2026-04-20",
        "currency": "RON",
        "seller": {
            "name": "Acme Romania SRL",
            "vat_id": "RO12345678",
            "country_code": "RO",
        },
        "buyer": {
            "name": "Globex Romania SRL",
            "vat_id": "RO87654328",
            "country_code": "RO",
        },
        "lines": [
            {
                "line_id": "1",
                "description": "RO e-Factura evaluation workflow",
                "quantity": "1",
                "unit_price": "1000.00",
                "vat_rate": "21",
                "line_extension_amount": "1000.00",
                "tax_amount": "210.00",
                "total_amount": "1210.00",
            }
        ],
        "totals": {
            "tax_exclusive_amount": "1000.00",
            "tax_amount": "210.00",
            "tax_inclusive_amount": "1210.00",
            "payable_amount": "1210.00",
        },
        "payment_terms": "Payment due within 30 days",
        "metadata": {"anaf_submission_context": "mock-spv-oauth"},
    }


@pytest.fixture
def spain_invoice() -> dict:
    return {
        "country": "ES",
        "transaction_type": "B2B",
        "invoice_number": "INV-ES-2026-0001",
        "issue_date": "2026-03-05",
        "currency": "EUR",
        "seller": {
            "name": "Acme Espana SL",
            "vat_id": "ESA12345674",
            "country_code": "ES",
        },
        "buyer": {
            "name": "Globex Espana SL",
            "vat_id": "ESB87654323",
            "country_code": "ES",
        },
        "lines": [
            {
                "line_id": "1",
                "description": "Local fiscal record workflow",
                "quantity": "1",
                "unit_price": "500.00",
                "vat_rate": "21",
                "line_extension_amount": "500.00",
                "tax_amount": "105.00",
                "total_amount": "605.00",
            }
        ],
        "totals": {
            "tax_exclusive_amount": "500.00",
            "tax_amount": "105.00",
            "tax_inclusive_amount": "605.00",
            "payable_amount": "605.00",
        },
        "payment_terms": "Payment due within 30 days",
        "metadata": {
            "sif_mode": "NO_VERIFACTU",
            "invoice_type": "F1",
            "software_producer_tax_id": "ESA12345674",
            "software_producer_name": "InvoiceBridge Labs SL",
            "software_system_id": "IB-EVAL-SIF-001",
            "software_system_code": "IB",
            "software_name": "InvoiceBridge SIF Test Harness",
            "software_version": "0.1.0",
            "installation_number": "IB-ES-INSTALL-001",
            "verifactu_capable": True,
            "only_verifactu_capable": False,
            "event_log_enabled": True,
            "record_timestamp": "2026-03-05T10:15:00+01:00",
            "previous_record_hash": "0" * 64,
            "previous_record_invoice_number": "INV-ES-2026-0000",
            "previous_record_issue_date": "2026-03-04",
            "previous_event_hash": "0" * 64,
            "responsible_declaration_reference": "IB-SIF-DECLARATION-DEMO-001",
        },
    }
