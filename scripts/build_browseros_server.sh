#!/usr/bin/env bash
# Build browseros_server from BrowserOS-agent and copy into this repo.
# Requires: git, bun (https://bun.sh)
# Usage:
#   ./scripts/build_browseros_server.sh              # current platform (requires: git submodule update --init packages/browseros-agent)
#   BROWSEROS_AGENT_DIR=/path/to/BrowserOS-agent ./scripts/build_browseros_server.sh  # use given clone
#   TARGET=linux-arm64 ./scripts/build_browseros_server.sh   # override target

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST_DIR="$REPO_ROOT/packages/browseros/resources/binaries/browseros_server"
AGENT_DIR="${BROWSEROS_AGENT_DIR:-}"
SUBMODULE_AGENT="$REPO_ROOT/packages/browseros-agent"

detect_target() {
  local os arch
  case "$(uname -s)" in
    Darwin)  os=darwin ;;
    Linux)   os=linux ;;
    MINGW*|MSYS*|CYGWIN*) os=windows ;;
    *)       echo "Unsupported OS: $(uname -s)" >&2; exit 1 ;;
  esac
  case "$(uname -m)" in
    x86_64|amd64|AMD64) arch=x64 ;;
    aarch64|arm64)      arch=arm64 ;;
    *)                 echo "Unsupported arch: $(uname -m)" >&2; exit 1 ;;
  esac
  if [[ "$os" == "windows" ]]; then
    echo "windows-x64"
  else
    echo "$os-$arch"
  fi
}

target_to_binary_name() {
  local t="$1"
  if [[ "$t" == "windows-x64" ]]; then
    echo "browseros-server-windows-x64.exe"
  else
    echo "browseros-server-$t"
  fi
}

main() {
  local target="${TARGET:-$(detect_target)}"
  local binary_name
  binary_name="$(target_to_binary_name "$target")"

  echo "Target: $target  ->  $binary_name"
  echo "Destination: $DEST_DIR"

  if [[ -z "$AGENT_DIR" ]]; then
    if [[ ! -e "$SUBMODULE_AGENT/.git" ]]; then
      echo "Error: git submodule packages/browseros-agent is not initialized." >&2
      echo "Run: git submodule update --init packages/browseros-agent" >&2
      exit 1
    fi
    AGENT_DIR="$SUBMODULE_AGENT"
    echo "Using git submodule at $AGENT_DIR"
  fi

  # Ensure we're building from code that won't crash in Bun bundle (no pino-pretty in bundle)
  LOGGER_TS="$AGENT_DIR/apps/server/src/lib/logger.ts"
  if [[ ! -f "$LOGGER_TS" ]]; then
    echo "Error: logger.ts not found at $LOGGER_TS" >&2
    exit 1
  fi
  if ! grep -A 5 'function createConsoleTransport' "$LOGGER_TS" | grep -q 'return null'; then
    echo "Error: logger createConsoleTransport() must return null (no pino-pretty in bundle)." >&2
    echo "See apps/server/src/lib/logger.ts" >&2
    exit 1
  fi
  echo "Verified: logger safe for Bun compile (our code)"

  cd "$AGENT_DIR"
  echo "Installing deps (bun install) ..."
  bun install

  # Build script expects apps/server/.env.development; create from example if missing
  if [[ ! -f "$AGENT_DIR/apps/server/.env.development" ]]; then
    echo "Creating apps/server/.env.development from .env.example ..."
    cp "$AGENT_DIR/apps/server/.env.example" "$AGENT_DIR/apps/server/.env.development"
  fi

  echo "Building server (--mode=dev --target=$target) ..."
  bun scripts/build/server.ts --mode=dev --target="$target"

  local src="$AGENT_DIR/dist/server/$binary_name"
  if [[ ! -f "$src" ]]; then
    echo "Build failed: $src not found" >&2
    exit 1
  fi

  mkdir -p "$DEST_DIR"
  cp "$src" "$DEST_DIR/"
  chmod +x "$DEST_DIR/$binary_name"
  echo "Done. Binary copied to $DEST_DIR/$binary_name (our build from $AGENT_DIR)"
}

main "$@"
