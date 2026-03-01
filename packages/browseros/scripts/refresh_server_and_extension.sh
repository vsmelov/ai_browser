#!/usr/bin/env bash
# Wrapper: run the real refresh script from repo root (so you can run from packages/browseros).
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
exec "$REPO_ROOT/scripts/refresh_server_and_extension.sh" "$@"
