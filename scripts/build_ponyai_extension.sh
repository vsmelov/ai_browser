#!/usr/bin/env bash
# Build the Agent Chrome extension (as-is from submodule; rebrand steps commented out).
# Requires: bun (https://bun.sh). Uses git submodule packages/browseros-agent (no .cache fallback).
# Build runs the same way as upstream: from monorepo root with "bun ci" and "bun run build:agent".
# Upstream expects bun 1.3.6 (engines in package.json). Use that version; clear bun cache once if needed: bun pm cache rm --global
#
# Usage:
#   ./scripts/build_ponyai_extension.sh
#   BROWSEROS_AGENT_DIR=/path/to/agent ./scripts/build_ponyai_extension.sh
#   BUILD_AGENT_WITHOUT_CLOUD=1 ./scripts/build_ponyai_extension.sh   # skip codegen (requires stub on struggle)
#
# Ensures: submodule at expected commit, clean working tree (no rebrand applied).
# After running: unpacked extension in packages/browseros/resources/extensions/agent-build/

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v bun >/dev/null 2>&1; then
  echo "Error: bun is required but not found. Install from https://bun.sh" >&2
  exit 1
fi
EXT_DEST="$REPO_ROOT/packages/browseros/resources/extensions"
# ICONS_SRC="$REPO_ROOT/packages/browseros/resources/icons"  # rebrand
AGENT_DIR="${BROWSEROS_AGENT_DIR:-}"
SUBMODULE_AGENT="$REPO_ROOT/packages/browseros-agent"

# --- Rebrand (commented out): uncomment when building with PonyClaw branding ---
# apply_rebrand() {
#   local agent_app="$1"
#   echo "Applying PonyClaw rebrand (display strings and URLs only) ..."
#   sed -i.bak "s/default_title: 'Ask BrowserOS'/default_title: 'Ask PonyClaw'/" "$agent_app/wxt.config.ts"
#   sed -i.bak "s|cdn.browseros.com|cdn.ponyai.com|g" "$agent_app/wxt.config.ts"
#   [[ -f "$agent_app/wxt.config.ts.bak" ]] && rm -f "$agent_app/wxt.config.ts.bak"
#   sed -i.bak "s/browseros.com/ponyai.com/g" "$agent_app/lib/constants/productWebHost.ts"
#   sed -i.bak "s/browseros.com/ponyai.com/g; s/browseros-ai/ponyai-ai/g" "$agent_app/lib/constants/productUrls.ts"
#   sed -i.bak "s/name: 'BrowserOS'/name: 'PonyClaw'/; s|api.browseros.com|api.ponyai.com|g" "$agent_app/lib/llm-providers/storage.ts"
#   sed -i.bak "s|docs.browseros.com|docs.ponyai.com|g; s/ label: 'BrowserOS'/ label: 'PonyClaw'/" "$agent_app/lib/llm-providers/providerTemplates.ts"
#   sed -i.bak 's/alt="BrowserOS"/alt="PonyClaw"/g' "$agent_app/lib/llm-providers/providerIcons.tsx"
#   for f in "$agent_app/entrypoints/onboarding/index/OnboardingHeader.tsx" "$agent_app/entrypoints/onboarding/steps/StepOne.tsx" \
#            "$agent_app/entrypoints/onboarding/index/Onboarding.tsx" "$agent_app/entrypoints/onboarding/features/Features.tsx" \
#            "$agent_app/entrypoints/sidepanel/index/ChatError.tsx" "$agent_app/entrypoints/sidepanel/index/JtbdPopup.tsx" \
#            "$agent_app/entrypoints/sidepanel/index/chatTypes.ts" "$agent_app/entrypoints/newtab/index/NewTabBranding.tsx" \
#            "$agent_app/entrypoints/app/ai-settings/LlmProvidersHeader.tsx" "$agent_app/entrypoints/newtab/personalize/Personalize.tsx" \
#            "$agent_app/lib/changelog/changelog-config.ts"; do
#     [[ -f "$f" ]] && sed -i.bak 's/BrowserOS/PonyClaw/g; s|browseros.com|ponyai.com|g; s|docs.browseros.com|docs.ponyai.com|g' "$f" && rm -f "${f}.bak"
#   done
#   echo "Rebrand applied."
# }
#
# copy_icons() {
#   local agent_app="$1"
#   local icon_dir="$agent_app/public/icon"
#   [[ -d "$agent_app/public" ]] || mkdir -p "$agent_app/public"
#   mkdir -p "$icon_dir"
#   echo "Copying PonyClaw icons to $icon_dir ..."
#   for size in 16 32 48 128; do
#     if [[ -f "$ICONS_SRC/product_logo_${size}.png" ]]; then
#       cp "$ICONS_SRC/product_logo_${size}.png" "$icon_dir/${size}.png"
#       echo "  ${size}.png"
#     fi
#   done
# }

patch_sourcemap_off() {
  local wxt_cfg="$1"
  if grep -q "sourcemap: 'hidden'" "$wxt_cfg" 2>/dev/null; then
    sed -i.bak "s/sourcemap: 'hidden'/sourcemap: false/" "$wxt_cfg"
    echo "  (source maps disabled in wxt.config.ts)"
  fi
}

main() {
  echo "=== Build PonyClaw extension (Agent) ==="
  echo "Destination: $EXT_DEST"
  echo ""

  if [[ -z "$AGENT_DIR" ]]; then
    if [[ ! -e "$SUBMODULE_AGENT/.git" ]]; then
      echo "Error: git submodule packages/browseros-agent is not initialized." >&2
      echo "Run: git submodule update --init packages/browseros-agent" >&2
      exit 1
    fi
    AGENT_DIR="$SUBMODULE_AGENT"
  fi
  local agent_app="$AGENT_DIR/apps/agent"
  echo "--- Step 1/7: Check BrowserOS-agent ---"
  if [[ ! -d "$agent_app" ]]; then
    echo "Error: BrowserOS-agent not found at $AGENT_DIR (no apps/agent)." >&2
    exit 1
  fi
  echo "  Using: $AGENT_DIR"
  echo ""

  echo "--- Step 1b/7: Bun version (upstream expects 1.3.6) ---"
  want_bun="1.3.6"
  current_bun="$(bun --version 2>/dev/null || true)"
  if [[ "$current_bun" != "$want_bun" ]]; then
    echo "Error: upstream expects bun $want_bun (see packages/browseros-agent/package.json engines). Current: $current_bun" >&2
    echo "Install matching version, e.g.: curl -fsSL https://bun.sh/install | bash -s bun-v${want_bun}" >&2
    exit 1
  fi
  echo "  bun $current_bun"
  echo ""

  # Require submodule at expected commit and clean tree (build as-is, no rebrand)
  if [[ "$AGENT_DIR" == "$SUBMODULE_AGENT" ]]; then
    expected_commit="$(cd "$REPO_ROOT" && git ls-tree HEAD packages/browseros-agent 2>/dev/null | awk '{print $3}')"
    if [[ -z "$expected_commit" ]]; then
      echo "Error: could not get expected submodule commit from parent repo (git ls-tree HEAD packages/browseros-agent)." >&2
      exit 1
    fi
    current_commit="$(cd "$AGENT_DIR" && git rev-parse HEAD)"
    if [[ "$current_commit" != "$expected_commit" ]]; then
      echo "Error: packages/browseros-agent is at $current_commit but parent repo expects $expected_commit." >&2
      echo "Run: cd packages/browseros-agent && git checkout $expected_commit" >&2
      exit 1
    fi
    echo "  Submodule at expected commit: ${expected_commit:0:7}"
    dirty="$(cd "$AGENT_DIR" && git status --porcelain)"
    # Ignore bun.lock (bun ci updates it) and apps/agent/lib/env.ts (zod/vite-node fix)
    dirty_other="$(echo "$dirty" | grep -v 'bun.lock$' | grep -v 'apps/agent/lib/env.ts' || true)"
    if [[ -n "$dirty_other" ]]; then
      echo "Error: packages/browseros-agent has local changes (dirty tree). Build as-is requires clean state." >&2
      echo "Changed files:" >&2
      echo "$dirty" | sed 's/^/  /' >&2
      exit 1
    fi
    if [[ -n "$dirty" ]]; then
      echo "  Working tree clean except bun.lock and apps/agent/lib/env.ts (ok)"
    else
      echo "  Working tree clean (no rebrand applied)"
    fi
  fi
  echo ""

  # --- Rebrand steps commented out (build as-is) ---
  # echo "--- Step 2/8: Apply PonyClaw rebrand ---"
  # apply_rebrand "$agent_app"
  # echo ""
  # echo "--- Step 3/8: Copy PonyClaw icons ---"
  # copy_icons "$agent_app"
  # echo ""

  echo "--- Step 2/7: Patch codegen (optional) ---"
  if [[ -f "$REPO_ROOT/scripts/agent-codegen.ts" ]]; then
    cp "$REPO_ROOT/scripts/agent-codegen.ts" "$agent_app/codegen.ts"
    echo "  Patched codegen.ts"
  else
    echo "  (skipped: scripts/agent-codegen.ts not found)"
  fi
  echo ""

  cd "$AGENT_DIR"
  echo "--- Step 3/7: Install deps (bun ci, same as upstream CI) ---"
  bun ci
  echo ""

  if [[ -f "$agent_app/.env.example" ]] && [[ ! -f "$agent_app/.env.development" ]]; then
    cp "$agent_app/.env.example" "$agent_app/.env.development"
    echo "  Created .env.development from .env.example"
  fi

  if [[ -n "${BUILD_AGENT_WITHOUT_CLOUD:-}" ]]; then
    if [[ ! -d "$REPO_ROOT/scripts/agent-generated-stub/generated/graphql" ]]; then
      echo "Error: BUILD_AGENT_WITHOUT_CLOUD=1 requires scripts/agent-generated-stub/ (present on struggle branch)." >&2
      echo "Run without BUILD_AGENT_WITHOUT_CLOUD to use in-repo schema (codegen)." >&2
      exit 1
    fi
    echo "--- Step 6/8: Prepare build WITHOUT cloud ---"
    mkdir -p "$agent_app/generated/graphql"
    cp -r "$REPO_ROOT/scripts/agent-generated-stub/generated/graphql/"* "$agent_app/generated/graphql"
    sed -i.bak 's/^    "build": "bun run codegen && wxt build",$/    "build": "wxt build",/' "$agent_app/package.json"
    patch_sourcemap_off "$agent_app/wxt.config.ts"
    trap '[[ -f "$agent_app/wxt.config.ts.bak" ]] && mv "$agent_app/wxt.config.ts.bak" "$agent_app/wxt.config.ts"; [[ -f "$agent_app/package.json.bak" ]] && mv "$agent_app/package.json.bak" "$agent_app/package.json"' EXIT
    echo ""
    echo "--- Step 6/7: Run wxt build ---"
    (cd "$agent_app" && bun --env-file=.env.development run build)
    trap - EXIT
    [[ -f "$agent_app/wxt.config.ts.bak" ]] && mv "$agent_app/wxt.config.ts.bak" "$agent_app/wxt.config.ts"
    [[ -f "$agent_app/package.json.bak" ]] && mv "$agent_app/package.json.bak" "$agent_app/package.json"
  else
    echo "--- Step 5/7: Disable source maps (required) ---"
    patch_sourcemap_off "$agent_app/wxt.config.ts"
    trap '[[ -f "$agent_app/wxt.config.ts.bak" ]] && mv "$agent_app/wxt.config.ts.bak" "$agent_app/wxt.config.ts"' EXIT
    echo ""
    echo "--- Step 6/7: Run build:agent (same as upstream: from monorepo root) ---"
    GRAPHQL_SCHEMA_PATH="$agent_app/schema/schema.graphql"
    if [[ ! -f "$GRAPHQL_SCHEMA_PATH" ]]; then
      echo "Error: GraphQL schema not found at $GRAPHQL_SCHEMA_PATH" >&2
      exit 1
    fi
    export GRAPHQL_SCHEMA_PATH
    (cd "$AGENT_DIR" && bun run build:agent)
    trap - EXIT
    [[ -f "$agent_app/wxt.config.ts.bak" ]] && mv "$agent_app/wxt.config.ts.bak" "$agent_app/wxt.config.ts"
  fi

  echo ""
  echo "--- Step 7/7: Copy to agent-build ---"
  local out_dir="$agent_app/dist/chrome-mv3"
  [[ ! -d "$out_dir" ]] && out_dir="$agent_app/dist"
  [[ ! -d "$out_dir" ]] && out_dir="$agent_app/.output/chrome-mv3"
  [[ ! -d "$out_dir" ]] && out_dir="$agent_app/.output"
  if [[ ! -d "$out_dir" ]]; then
    echo "Build failed: dist not found in $agent_app" >&2
    exit 1
  fi
  mkdir -p "$EXT_DEST"
  rm -rf "$EXT_DEST/agent-build"
  cp -r "$out_dir" "$EXT_DEST/agent-build"
  echo "  Copied to: $EXT_DEST/agent-build/"
  echo ""
  echo "Done. Unpacked extension: $EXT_DEST/agent-build/"
}

main "$@"
