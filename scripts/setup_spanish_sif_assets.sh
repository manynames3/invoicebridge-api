#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR="${1:-vendor/spanish-sif}"
BASE_URL="https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tikeV1.0/cont/ws"

mkdir -p "$TARGET_DIR"

download() {
  local name="$1"
  curl -fsSL "$BASE_URL/$name" -o "$TARGET_DIR/$name"
}

download "SistemaFacturacion.wsdl"
download "SuministroInformacion.xsd"
download "SuministroLR.xsd"
download "ConsultaLR.xsd"
download "RespuestaSuministro.xsd"
download "RespuestaConsultaLR.xsd"

curl -fsSL "https://www.w3.org/TR/xmldsig-core/xmldsig-core-schema.xsd" \
  -o "$TARGET_DIR/xmldsig-core-schema.xsd"

"${PYTHON:-python3}" - "$TARGET_DIR/SuministroInformacion.xsd" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
text = text.replace(
    'schemaLocation="http://www.w3.org/TR/xmldsig-core/xmldsig-core-schema.xsd"',
    'schemaLocation="xmldsig-core-schema.xsd"',
)
path.write_text(text, encoding="utf-8")
PY

cat > "$TARGET_DIR/validate-spanish-sif.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
xmllint --noout --schema "$SCRIPT_DIR/SuministroLR.xsd" "$1"
SH

chmod +x "$TARGET_DIR/validate-spanish-sif.sh"

echo "SPANISH_SIF_VALIDATOR_COMMAND=$TARGET_DIR/validate-spanish-sif.sh {xml}"
