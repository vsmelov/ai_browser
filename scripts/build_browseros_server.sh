#!/usr/bin/env bash
# Build browseros_server from BrowserOS-agent and copy into this repo.
# Requires: git, bun (https://bun.sh)
# Usage:
#   ./scripts/build_browseros_server.sh              # current platform
#   BROWSEROS_AGENT_DIR=/path/to/BrowserOS-agent ./scripts/build_browseros_server.sh  # use existing clone
#   TARGET=linux-arm64 ./scripts/build_browseros_server.sh   # override target

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST_DIR="$REPO_ROOT/packages/browseros/resources/binaries/browseros_server"
AGENT_DIR="${BROWSEROS_AGENT_DIR:-}"
CLONE_DIR="$REPO_ROOT/.cache/BrowserOS-agent"

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
    AGENT_DIR="$CLONE_DIR"
  fi
  if [[ ! -d "$AGENT_DIR/apps/server" ]]; then
    echo "Error: BrowserOS-agent not found at $AGENT_DIR (no apps/server)." >&2
    echo "Clone it manually: git clone https://github.com/browseros-ai/BrowserOS-agent.git $AGENT_DIR" >&2
    exit 1
  fi

  cd "$AGENT_DIR"
  echo "Installing deps (bun install) ..."
  bun install

  # Build script expects apps/server/.env.development; create from example if missing
  if [[ ! -f "$AGENT_DIR/apps/server/.env.development" ]]; then
    echo "Creating apps/server/.env.development from .env.example ..."
    cp "$AGENT_DIR/apps/server/.env.example" "$AGENT_DIR/apps/server/.env.development"
  fi

  # Patch logger: disable pino-pretty for standalone binary (Bun compile can't resolve it).
  # createConsoleTransport() returns null in prod; in dev it returns { target: 'pino-pretty' } which
  # fails at runtime in the compiled binary. Force production logging path for our build.
  LOGGER_SRC="$AGENT_DIR/apps/server/src/lib/logger.ts"
  if grep -q "if (isDev)" "$LOGGER_SRC" 2>/dev/null; then
    echo "Patching logger.ts to skip pino-pretty in standalone build ..."
    sed -i.bak 's/if (isDev) {/if (false \&\& isDev) { \/\/ disabled for standalone: pino-pretty not available in Bun compile/' "$LOGGER_SRC" || true
  fi

  echo "Building server (--mode=dev --target=$target) ..."
  bun scripts/build/server.ts --mode=dev --target="$target"

  # Restore logger if we patched it
  if [[ -f "${LOGGER_SRC}.bak" ]]; then
    mv "${LOGGER_SRC}.bak" "$LOGGER_SRC"
  fi

  local src="$AGENT_DIR/dist/server/$binary_name"
  if [[ ! -f "$src" ]]; then
    echo "Build failed: $src not found" >&2
    exit 1
  fi

  mkdir -p "$DEST_DIR"
  cp "$src" "$DEST_DIR/"
  chmod +x "$DEST_DIR/$binary_name"
  echo "Done. Binary copied to $DEST_DIR/$binary_name"
}

main "$@"
