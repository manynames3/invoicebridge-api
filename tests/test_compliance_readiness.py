import sys

from fastapi.testclient import TestClient

from app.core.config import get_settings


def test_germany_is_not_production_ready_without_official_validator(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.get(
        "/v1/compliance/production-readiness",
        params={"country": "DE", "transaction_type": "B2B"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["country"] == "DE"
    assert body["production_ready"] is False
    assert body["no_paid_network_path"] is True
    assert "official_xrechnung_validation" in {
        requirement["code"] for requirement in body["requirements"] if requirement["status"] == "missing"
    }


def test_poland_readiness_exposes_free_direct_api_blockers(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.get(
        "/v1/compliance/production-readiness",
        params={"country": "PL", "transaction_type": "B2B"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["production_ready"] is False
    assert body["no_paid_network_path"] is True
    missing_codes = {requirement["code"] for requirement in body["requirements"] if requirement["status"] == "missing"}
    assert {"ksef_schema_validation", "ksef_api_endpoint", "ksef_credentials"} <= missing_codes


def test_spain_readiness_exposes_sif_production_blockers(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.get(
        "/v1/compliance/production-readiness",
        params={"country": "ES", "transaction_type": "B2B"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["production_ready"] is False
    missing_codes = {requirement["code"] for requirement in body["requirements"] if requirement["status"] == "missing"}
    assert {
        "spanish_sif_validation",
        "spanish_sif_signing",
        "spanish_sif_event_log",
        "spanish_aeat_test_portal_validation",
        "spanish_verifactu_submission_capability",
        "spanish_responsible_declaration",
    } <= missing_codes


def test_spain_readiness_passes_only_when_external_controls_are_configured(
    client: TestClient,
    auth_headers: dict[str, str],
    monkeypatch,
) -> None:
    monkeypatch.setenv("SPANISH_SIF_VALIDATOR_COMMAND", "true {xml}")
    monkeypatch.setenv("SPANISH_SIF_SIGNING_CONFIGURED", "true")
    monkeypatch.setenv("SPANISH_SIF_EVENT_LOG_CONFIGURED", "true")
    monkeypatch.setenv("SPANISH_SIF_RESPONSIBLE_DECLARATION_READY", "true")
    monkeypatch.setenv("SPANISH_SIF_AEAT_TEST_PORTAL_VALIDATED", "true")
    monkeypatch.setenv("SPANISH_VERIFACTU_SUBMISSION_CAPABLE", "true")
    get_settings.cache_clear()

    response = client.get(
        "/v1/compliance/production-readiness",
        params={"country": "ES", "transaction_type": "B2B"},
        headers=auth_headers,
    )

    get_settings.cache_clear()

    assert response.status_code == 200
    body = response.json()
    assert body["production_ready"] is True
    assert body["blocker_summary"] == []


def test_official_validation_is_explicit_when_validator_is_not_configured(
    client: TestClient,
    auth_headers: dict[str, str],
    germany_invoice: dict,
) -> None:
    transformed = client.post("/v1/invoices/transform", json=germany_invoice, headers=auth_headers)
    invoice_id = transformed.json()["invoice_id"]

    response = client.post(f"/v1/invoices/{invoice_id}/official-validate", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["configured"] is False
    assert body["passed"] is False
    assert body["validator_name"] == "XRechnung/EN16931 validator"


def test_official_validation_runs_configured_command(
    client: TestClient,
    auth_headers: dict[str, str],
    germany_invoice: dict,
    tmp_path,
    monkeypatch,
) -> None:
    validator = tmp_path / "validator.py"
    validator.write_text(
        "import pathlib, sys\n"
        "pathlib.Path(sys.argv[1]).read_text()\n"
        "raise SystemExit(0)\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("XRECHNUNG_VALIDATOR_COMMAND", f"{sys.executable} {validator} {{xml}}")
    get_settings.cache_clear()

    transformed = client.post("/v1/invoices/transform", json=germany_invoice, headers=auth_headers)
    invoice_id = transformed.json()["invoice_id"]
    response = client.post(f"/v1/invoices/{invoice_id}/official-validate", headers=auth_headers)

    get_settings.cache_clear()

    assert response.status_code == 200
    body = response.json()
    assert body["configured"] is True
    assert body["passed"] is True
    assert body["exit_code"] == 0


def test_spain_responsible_declaration_draft_endpoint(
    client: TestClient,
    auth_headers: dict[str, str],
    spain_invoice: dict,
) -> None:
    transformed = client.post("/v1/invoices/transform", json=spain_invoice, headers=auth_headers)
    invoice_id = transformed.json()["invoice_id"]

    response = client.get(f"/v1/invoices/{invoice_id}/spain/responsible-declaration", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["country"] == "ES"
    assert body["status"] == "draft_not_legal_advice"
    assert body["software"]["verifactu_capable"] is True
    assert "AEAT external test portal evidence" in body["external_requirements"]
