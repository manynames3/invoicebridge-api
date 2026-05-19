#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR="${1:-vendor/xrechnung}"
VALIDATOR_VERSION="${XRECHNUNG_VALIDATOR_VERSION:-1.6.0}"
CONFIG_VERSION="${XRECHNUNG_CONFIG_VERSION:-2026-01-31}"
CONFIG_TAG="${XRECHNUNG_CONFIG_TAG:-v2026-01-31}"
CONFIG_ZIP_NAME="xrechnung-3.0.2-validator-configuration-${CONFIG_VERSION}.zip"

VALIDATOR_URL="https://github.com/itplr-kosit/validator/releases/download/v${VALIDATOR_VERSION}/validator-${VALIDATOR_VERSION}.zip"
CONFIG_URL="https://github.com/itplr-kosit/validator-configuration-xrechnung/releases/download/${CONFIG_TAG}/${CONFIG_ZIP_NAME}"

mkdir -p "$TARGET_DIR"
tmp_dir="$(mktemp -d)"
cleanup() {
  rm -rf "$tmp_dir"
}
trap cleanup EXIT

curl -fsSL "$VALIDATOR_URL" -o "$tmp_dir/validator.zip"
curl -fsSL "$CONFIG_URL" -o "$tmp_dir/configuration.zip"

rm -rf "$TARGET_DIR/validator" "$TARGET_DIR/configuration"
mkdir -p "$TARGET_DIR/validator" "$TARGET_DIR/configuration"
unzip -q "$tmp_dir/validator.zip" -d "$TARGET_DIR/validator"
unzip -q "$tmp_dir/configuration.zip" -d "$TARGET_DIR/configuration"

cat >"$TARGET_DIR/validate-xrechnung.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail

if [ "\$#" -ne 1 ]; then
  echo "usage: validate-xrechnung.sh <invoice.xml>" >&2
  exit 2
fi

SCRIPT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="\$(cd "\$(dirname "\$1")" && pwd)"
java -jar "\$SCRIPT_DIR/validator/validator-${VALIDATOR_VERSION}-standalone.jar" \
  -r "\$SCRIPT_DIR/configuration" \
  -s "\$SCRIPT_DIR/configuration/scenarios.xml" \
  -o "\$OUTPUT_DIR" \
  -h "\$1"
EOF
chmod +x "$TARGET_DIR/validate-xrechnung.sh"

cat <<EOF
XRechnung validator installed at $TARGET_DIR

Set:
XRECHNUNG_VALIDATOR_COMMAND=$TARGET_DIR/validate-xrechnung.sh {xml}
EOF
