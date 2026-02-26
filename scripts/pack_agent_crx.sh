#!/usr/bin/env bash
# Pack the built extension (agent-build) to .crx from the command line.
# Requires: node/npx (npm install -g npx or use node from path)
#
# Usage:
#   ./scripts/pack_agent_crx.sh
#   EXTENSION_PACK_KEY=/path/to/agent.pem ./scripts/pack_agent_crx.sh
#
# If you have no .pem key yet: pack once in Chrome (chrome://extensions -> Pack extension),
# save the .pem file as packages/browseros/resources/extensions/agent.pem, then run this script.
# Same key => same extension ID (bflpfmnmnokmjhmgnolecpppdbdophmk), so bundled_extensions.json works as-is.

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXT_DIR="$REPO_ROOT/packages/browseros/resources/extensions"
AGENT_BUILD="$EXT_DIR/agent-build"
OUT_CRX="$EXT_DIR/bflpfmnmnokmjhmgnolecpppdbdophmk.crx"
KEY_FILE="${EXTENSION_PACK_KEY:-$EXT_DIR/agent.pem}"

if [[ ! -d "$AGENT_BUILD" ]]; then
  echo "Error: $AGENT_BUILD not found. Build the extension first: BUILD_AGENT_WITHOUT_CLOUD=1 ./scripts/build_ponyai_extension.sh" >&2
  exit 1
fi

pack_with_npx() {
  if [[ -f "$KEY_FILE" ]]; then
    npx --yes crx3 "$AGENT_BUILD" -o "$OUT_CRX" -p "$KEY_FILE"
    echo "Done: $OUT_CRX (extension ID bflpfmnmnokmjhmgnolecpppdbdophmk, ready for bundled_extensions.json)"
  else
    PACK_CRX="$EXT_DIR/agent-pack.crx"
    npx --yes crx3 "$AGENT_BUILD" -o "$PACK_CRX" -z
    echo "Done: $PACK_CRX (no key: new extension ID inside)."
    echo "Load it in Chrome (chrome://extensions) to see the ID, then rename to <id>.crx and update bundled_extensions.json."
    echo "To get stable ID next time: pack once in Chrome, save the .pem as $EXT_DIR/agent.pem, then run this script again."
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
    echo "Done: $OUT_CRX (extension ID bflpfmnmnokmjhmgnolecpppdbdophmk, ready for bundled_extensions.json)"
  else
    PACK_CRX="$EXT_DIR/agent-pack.crx"
    python3 "$py_script" "$AGENT_BUILD" "$PACK_CRX"
    echo "Done: $PACK_CRX (no key: new extension ID inside)."
    echo "Load it in Chrome (chrome://extensions) to see the ID, then rename to <id>.crx and update bundled_extensions.json."
    echo "Key saved next to .crx (agent-pack.pem); copy to $EXT_DIR/agent.pem for stable ID next time."
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
