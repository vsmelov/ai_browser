#!/usr/bin/env bash
# Fix side_panel_api.h duplicated patch: revert file in Chromium then re-run prep so patch applies once.
# Usage: CHROMIUM_SRC=/path/to/chromium/src ./scripts/fix_duplicate_side_panel_patch.sh

set -e
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHROMIUM_SRC="${CHROMIUM_SRC:-}"

if [[ -z "$CHROMIUM_SRC" || ! -d "$CHROMIUM_SRC" ]]; then
  echo "Error: CHROMIUM_SRC not set or missing. Example: export CHROMIUM_SRC=/path/to/chromium/src" >&2
  exit 1
fi

FILE="chrome/browser/extensions/api/side_panel/side_panel_api.h"
echo "Reverting $FILE in Chromium (removes duplicate BrowserOS classes) ..."
(cd "$CHROMIUM_SRC" && git checkout -- "$FILE")
echo "Done. Now run prep so the patch applies once:"
echo "  cd $REPO_ROOT/packages/browseros && uv run browseros build --chromium-src \"$CHROMIUM_SRC\" --prep"
echo "Then: cd \"$CHROMIUM_SRC\" && ninja -C out/Default_x64"
