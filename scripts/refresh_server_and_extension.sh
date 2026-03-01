#!/usr/bin/env bash
# Rebuild server (with pino fix) + extension, then prep Chromium so only a short ninja is needed.
# Use when you changed extension or server and want to avoid full browser recompile.
#
# Usage:
#   ./scripts/refresh_server_and_extension.sh
#   BROWSEROS_AGENT_DIR=/path/to/BrowserOS-agent ./scripts/refresh_server_and_extension.sh
#   CHROMIUM_SRC=/path/to/chromium/src ./scripts/refresh_server_and_extension.sh
#   SKIP_PACK=1 ./scripts/refresh_server_and_extension.sh   # skip .crx pack if you already have it
#
# Prep resets all patch targets in Chromium to HEAD then applies patches (avoids double-apply).
# After this script: run ninja in Chromium (see end of script). Ninja will only re-run copy
# targets for extensions and server resources — no C++ recompile.

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHROMIUM_SRC="${CHROMIUM_SRC:-}"
PACKAGES="$REPO_ROOT/packages/browseros"

# Log and run command; on failure print message and exit with 1.
run_or_exit() {
  local step="$1"
  shift
  echo ""
  echo "Running: $*"
  echo ""
  if ! "$@"; then
    echo "Error: $step failed (exit $?)" >&2
    exit 1
  fi
}

cd "$REPO_ROOT"
echo "PWD=$PWD"

echo ""
echo "=== 1. Rebuild BrowserOS server (with pino-pretty disabled for standalone) ==="
run_or_exit "Step 1 (build_browseros_server)" ./scripts/build_browseros_server.sh

echo ""
echo "=== 2. Rebuild extension (PonyAI) ==="
run_or_exit "Step 2 (build_ponyai_extension)" env BUILD_AGENT_WITHOUT_CLOUD=1 ./scripts/build_ponyai_extension.sh

BUNDLED_JSON="$PACKAGES/resources/extensions/bundled_extensions.json"
MANIFEST_BUILD="$PACKAGES/resources/extensions/agent-build/manifest.json"
echo "Verify extension version (expected from bundled_extensions.json) ..."
run_or_exit "Verify extension (manifest version)" python3 "$REPO_ROOT/scripts/verify_extension_bundle.py" --bundled-json "$BUNDLED_JSON" --manifest "$MANIFEST_BUILD"

echo ""
echo "=== 3. Pack extension to .crx (needed for bundled install) ==="
if [[ -n "${SKIP_PACK:-}" ]]; then
  echo "  SKIP_PACK=1, skip pack (step 3)."
elif [[ -d "$PACKAGES/resources/extensions/agent-build" ]]; then
  run_or_exit "Step 3 (pack_agent_crx)" ./scripts/pack_agent_crx.sh
  echo "  Packed .crx ready."
  CRX_NAME=$(python3 -c "import json; d=json.load(open('$BUNDLED_JSON')); k=next(iter(d)); print(d[k].get('external_crx',''))")
  if [[ -n "$CRX_NAME" && -f "$PACKAGES/resources/extensions/$CRX_NAME" ]]; then
    echo "Verify packed .crx (ID and version) ..."
    run_or_exit "Verify extension (.crx ID and version)" python3 "$REPO_ROOT/scripts/verify_extension_bundle.py" --bundled-json "$BUNDLED_JSON" --manifest "$MANIFEST_BUILD" --crx "$PACKAGES/resources/extensions/$CRX_NAME"
  fi
else
  echo "Error: agent-build not found at $PACKAGES/resources/extensions/agent-build (required for step 3)." >&2
  exit 1
fi

echo ""
echo "=== 4. Prep Chromium (copy resources + bundled_extensions into tree, run configure) ==="
if [[ -z "$CHROMIUM_SRC" ]]; then
  CHROMIUM_SRC="$REPO_ROOT/chromium/src"
  if [[ ! -d "$CHROMIUM_SRC" ]]; then
    CHROMIUM_SRC=""
  fi
fi
if [[ -z "$CHROMIUM_SRC" || ! -d "$CHROMIUM_SRC" ]]; then
  echo "Error: CHROMIUM_SRC not set or directory missing. Set it and re-run, then run prep and ninja manually." >&2
  echo "  export CHROMIUM_SRC=/path/to/chromium/src" >&2
  echo "  cd $PACKAGES && uv run browseros build --chromium-src \"\$CHROMIUM_SRC\" --prep" >&2
  echo "  cd \"\$CHROMIUM_SRC\" && ninja -C out/Default_x64" >&2
  exit 1
fi

cd "$PACKAGES"
echo "PWD=$PWD"
run_or_exit "Step 4 (browseros build --prep)" uv run browseros build --chromium-src "$CHROMIUM_SRC" --prep

echo ""
echo "=== 5. Short ninja (only changed copy targets, no full recompile) ==="
cd "$CHROMIUM_SRC"
echo "PWD=$PWD"
run_or_exit "Step 5 (ninja)" ninja -C out/Default_x64

echo ""
echo "Done. Run the browser: $CHROMIUM_SRC/out/Default_x64/ponyai --user-data-dir=/tmp/browseros-test --enable-logging=stderr"
