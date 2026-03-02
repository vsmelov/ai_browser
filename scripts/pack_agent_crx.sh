#!/usr/bin/env bash
# Pack the built extension (agent-build) to .crx from the command line.
# Requires: npx (Node.js) or Python with crx3.
#
# Usage:
#   ./scripts/pack_agent_crx.sh
#   EXTENSION_PACK_KEY=/path/to/agent.pem ./scripts/pack_agent_crx.sh
#
# If you have no .pem key yet: pack once in Chrome (chrome://extensions -> Pack extension),
# save the .pem file as packages/browseros/resources/extensions/agent.pem, then run this script.
# Same key => same extension ID; fork uses our key (ijlpinlejblenhkmjpgbjglcjibmlenp). Update bundled_extensions.json with that ID.

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXT_DIR="$REPO_ROOT/packages/browseros/resources/extensions"
AGENT_BUILD="$EXT_DIR/agent-build"
OUT_CRX="$EXT_DIR/agent-pack.crx"
KEY_FILE="${EXTENSION_PACK_KEY:-$EXT_DIR/agent.pem}"

if [[ ! -d "$AGENT_BUILD" ]]; then
  echo "Error: $AGENT_BUILD not found. Build the extension first: ./scripts/build_ponyai_extension.sh" >&2
  exit 1
fi

print_result() {
  echo ""
  echo "Output file:  agent-pack.crx"
  echo "Full path:    $OUT_CRX"
  if [[ -f "$OUT_CRX" ]]; then
    echo "Size:         $(stat -c%s "$OUT_CRX" 2>/dev/null | awk '{printf "%.1f MB", $1/1024/1024}' || echo "—")"
  fi
  if [[ -f "$REPO_ROOT/scripts/get_crx_extension_id.py" && -f "$OUT_CRX" ]]; then
    echo ""
    python3 "$REPO_ROOT/scripts/get_crx_extension_id.py" "$OUT_CRX"
  fi
}

pack_with_npx() {
  if [[ -f "$KEY_FILE" ]]; then
    npx --yes crx3 "$AGENT_BUILD" -o "$OUT_CRX" -p "$KEY_FILE"
    echo "Done (signed with key)."
    print_result
  else
    npx --yes crx3 "$AGENT_BUILD" -o "$OUT_CRX" -z
    echo "Done (no key: new ID; copy agent-pack.pem → agent.pem for stable ID next time)."
    print_result
    echo ""
    echo "To write bundled_extensions.json:  python3 $REPO_ROOT/scripts/get_crx_extension_id.py $OUT_CRX --write-json"
  fi
}

pack_with_python() {
  local py_script="$REPO_ROOT/scripts/pack_agent_crx.py"
  if ! python3 -c "from crx3 import creator" 2>/dev/null; then
    echo "Error: Python package 'crx3' not found. Install it: pip install --user crx3" >&2
    exit 1
  fi
  if [[ -f "$KEY_FILE" ]]; then
    python3 "$py_script" "$AGENT_BUILD" "$OUT_CRX" "$KEY_FILE"
    echo "Done (signed with key)."
    print_result
  else
    python3 "$py_script" "$AGENT_BUILD" "$OUT_CRX"
    echo "Done (no key: new ID; key saved as agent-pack.pem)."
    print_result
    echo ""
    echo "To write bundled_extensions.json:  python3 $REPO_ROOT/scripts/get_crx_extension_id.py $OUT_CRX --write-json"
  fi
}

echo "Packing extension from $AGENT_BUILD ..."

if command -v npx >/dev/null 2>&1; then
  pack_with_npx
elif python3 -c "from crx3 import creator" 2>/dev/null; then
  pack_with_python
else
  echo "Error: need either Node.js (npx) or Python with crx3." >&2
  echo "  Node:  apt install nodejs npm   (or install Node from nodejs.org)" >&2
  echo "  Python: pip install --user crx3" >&2
  exit 1
fi
