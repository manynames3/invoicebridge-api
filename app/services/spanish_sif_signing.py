import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from app.core.config import Settings, get_settings
from app.services.checksum import stable_payload_hash


@dataclass(frozen=True)
class SpanishSIFSigningResult:
    configured: bool
    signed_xml: str
    signature_reference: str | None
    message: str


def sign_spanish_sif_document(
    xml: str,
    *,
    settings: Settings | None = None,
) -> SpanishSIFSigningResult:
    active_settings = settings or get_settings()
    command = active_settings.spanish_sif_signing_command
    if not command:
        return SpanishSIFSigningResult(
            configured=False,
            signed_xml=xml,
            signature_reference=None,
            message="SPANISH_SIF_SIGNING_COMMAND is not configured.",
        )

    with TemporaryDirectory() as temp_dir:
        xml_path = Path(temp_dir) / "spanish-sif.xml"
        xml_path.write_text(xml, encoding="utf-8")
        command_text = command.replace("{xml}", shlex.quote(str(xml_path)))
        if "{xml}" not in command:
            command_text = f"{command_text} {shlex.quote(str(xml_path))}"
        completed = subprocess.run(
            command_text,
            shell=True,
            cwd=temp_dir,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "Spanish SIF signing command failed: "
                f"{(completed.stderr or completed.stdout or '').strip()[:500]}"
            )
        signed_xml = completed.stdout.strip() or xml_path.read_text(encoding="utf-8")
        return SpanishSIFSigningResult(
            configured=True,
            signed_xml=signed_xml,
            signature_reference=stable_payload_hash(signed_xml)[:24],
            message="Spanish SIF signing command completed.",
        )
