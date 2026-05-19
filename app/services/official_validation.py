import shlex
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from app.core.config import Settings, get_settings
from app.db.models import Invoice
from app.schemas.compliance import OfficialValidationResponse


def validate_official_document(
    invoice: Invoice,
    xml: str,
    *,
    settings: Settings | None = None,
) -> OfficialValidationResponse:
    active_settings = settings or get_settings()
    validator_name, command = _validator_for_invoice(invoice, active_settings)
    if not command:
        return OfficialValidationResponse(
            invoice_id=invoice.id,
            country=invoice.country,
            required_format=invoice.required_format,
            validator_name=validator_name,
            configured=False,
            passed=False,
            message=f"{validator_name} is not configured for this deployment.",
        )

    with TemporaryDirectory() as temp_dir:
        document = Path(temp_dir) / "invoice.xml"
        document.write_text(xml, encoding="utf-8")
        args = _command_args(command, str(document))
        completed = subprocess.run(args, cwd=temp_dir, capture_output=True, text=True, timeout=60, check=False)

    return OfficialValidationResponse(
        invoice_id=invoice.id,
        country=invoice.country,
        required_format=invoice.required_format,
        validator_name=validator_name,
        configured=True,
        passed=completed.returncode == 0,
        exit_code=completed.returncode,
        message="Official validator command passed." if completed.returncode == 0 else "Official validator failed.",
        stdout_excerpt=_excerpt(completed.stdout),
        stderr_excerpt=_excerpt(completed.stderr),
    )


def _validator_for_invoice(invoice: Invoice, settings: Settings) -> tuple[str, str | None]:
    if invoice.country == "DE":
        return "XRechnung/EN16931 validator", settings.xrechnung_validator_command
    if invoice.country == "PL":
        return "KSeF FA schema validator", settings.ksef_schema_validator_command
    if invoice.country == "RO":
        return "RO e-Factura/RO_CIUS validator", settings.ro_efactura_schema_validator_command
    if invoice.country == "ES":
        return "Spanish SIF/VERI*FACTU validator", settings.spanish_sif_validator_command
    return "Official country validator", None


def _command_args(command: str, xml_path: str) -> list[str]:
    args = shlex.split(command)
    if "{xml}" in args:
        return [arg if arg != "{xml}" else xml_path for arg in args]
    return [*args, xml_path]


def _excerpt(value: str) -> str | None:
    stripped = value.strip()
    if not stripped:
        return None
    return stripped[:2000]
