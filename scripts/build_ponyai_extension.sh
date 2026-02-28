#!/usr/bin/env bash
# Build the Agent Chrome extension with PonyAI branding and copy into this repo.
# Requires: git, bun (https://bun.sh)
#
# Usage:
#   ./scripts/build_ponyai_extension.sh
#   BROWSEROS_AGENT_DIR=/path/to/BrowserOS-agent ./scripts/build_ponyai_extension.sh
#   BUILD_AGENT_WITHOUT_CLOUD=1 ./scripts/build_ponyai_extension.sh   # skip codegen, use stub (no schema/API needed)
#
# Log to file: BUILD_AGENT_WITHOUT_CLOUD=1 ./scripts/build_ponyai_extension.sh 2>&1 | tee extension-build.log
# Unbuffered log (see progress live): stdbuf -oL -eL bash -c 'BUILD_AGENT_WITHOUT_CLOUD=1 ./scripts/build_ponyai_extension.sh' 2>&1 | tee extension-build.log
#
# After running:
#   - Unpacked extension is in packages/browseros/resources/extensions/agent-build/
#   - To use as bundled: pack that folder to .crx (Chrome -> Extensions -> Pack extension),
#     put the .crx and bundled_extensions.json in resources/extensions/ (see README there).

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v bun >/dev/null 2>&1; then
  echo "Error: bun is required but not found. Install from https://bun.sh (e.g. curl -fsSL https://bun.sh/install | bash)" >&2
  exit 1
fi
EXT_DEST="$REPO_ROOT/packages/browseros/resources/extensions"
ICONS_SRC="$REPO_ROOT/packages/browseros/resources/icons"
AGENT_DIR="${BROWSEROS_AGENT_DIR:-}"
CLONE_DIR="$REPO_ROOT/.cache/BrowserOS-agent"

apply_rebrand() {
  local agent_app="$1"
  echo "Applying PonyAI rebrand (display strings and URLs only) ..."
  # Only replace in user-facing files; do NOT replace @browseros, type: 'browseros', browseros.* API names
  sed -i.bak "s/default_title: 'Ask BrowserOS'/default_title: 'Ask PonyAI'/" "$agent_app/wxt.config.ts"
  sed -i.bak "s|cdn.browseros.com|cdn.ponyai.com|g" "$agent_app/wxt.config.ts"
  [[ -f "$agent_app/wxt.config.ts.bak" ]] && rm -f "$agent_app/wxt.config.ts.bak"
  sed -i.bak "s/browseros.com/ponyai.com/g" "$agent_app/lib/constants/productWebHost.ts"
  sed -i.bak "s/browseros.com/ponyai.com/g; s/browseros-ai/ponyai-ai/g" "$agent_app/lib/constants/productUrls.ts"
  sed -i.bak "s/name: 'BrowserOS'/name: 'PonyAI'/; s|api.browseros.com|api.ponyai.com|g" "$agent_app/lib/llm-providers/storage.ts"
  sed -i.bak "s|docs.browseros.com|docs.ponyai.com|g; s/ label: 'BrowserOS'/ label: 'PonyAI'/" "$agent_app/lib/llm-providers/providerTemplates.ts"
  sed -i.bak 's/alt="BrowserOS"/alt="PonyAI"/g' "$agent_app/lib/llm-providers/providerIcons.tsx"
  for f in "$agent_app/entrypoints/onboarding/index/OnboardingHeader.tsx" "$agent_app/entrypoints/onboarding/steps/StepOne.tsx" \
           "$agent_app/entrypoints/onboarding/index/Onboarding.tsx" "$agent_app/entrypoints/onboarding/features/Features.tsx" \
           "$agent_app/entrypoints/sidepanel/index/ChatError.tsx" "$agent_app/entrypoints/sidepanel/index/JtbdPopup.tsx" \
           "$agent_app/entrypoints/sidepanel/index/chatTypes.ts" "$agent_app/entrypoints/newtab/index/NewTabBranding.tsx" \
           "$agent_app/entrypoints/app/ai-settings/LlmProvidersHeader.tsx" "$agent_app/entrypoints/newtab/personalize/Personalize.tsx" \
           "$agent_app/lib/changelog/changelog-config.ts"; do
    [[ -f "$f" ]] && sed -i.bak 's/BrowserOS/PonyAI/g; s|browseros.com|ponyai.com|g; s|docs.browseros.com|docs.ponyai.com|g' "$f" && rm -f "${f}.bak"
  done
  echo "Rebrand applied."
}

copy_icons() {
  local agent_app="$1"
  # WXT expects icons at public/icon/16.png, 32.png, 48.png, 128.png (see wxt.config.ts)
  local icon_dir="$agent_app/public/icon"
  [[ -d "$agent_app/public" ]] || mkdir -p "$agent_app/public"
  mkdir -p "$icon_dir"
  echo "Copying PonyAI icons to $icon_dir ..."
  for size in 16 32 48 128; do
    if [[ -f "$ICONS_SRC/product_logo_${size}.png" ]]; then
      cp "$ICONS_SRC/product_logo_${size}.png" "$icon_dir/${size}.png"
      echo "  ${size}.png"
    fi
  done
}

main() {
  echo "=== Build PonyAI extension (Agent) ==="
  echo "Destination: $EXT_DEST"

  if [[ -z "$AGENT_DIR" ]]; then
    AGENT_DIR="$CLONE_DIR"
    if [[ ! -d "$AGENT_DIR/.git" ]]; then
      echo "Cloning BrowserOS-agent into $AGENT_DIR ..."
      mkdir -p "$(dirname "$AGENT_DIR")"
      git clone --depth 1 https://github.com/browseros-ai/BrowserOS-agent.git "$AGENT_DIR"
    else
      echo "Using existing clone at $AGENT_DIR (pull latest)"
      (cd "$AGENT_DIR" && git pull --depth 1 || true)
    fi
  fi

  local agent_app="$AGENT_DIR/apps/agent"
  if [[ ! -d "$agent_app" ]]; then
    echo "Error: apps/agent not found in $AGENT_DIR" >&2
    exit 1
  fi

  # Revert any previous rebrand so we start from clean (optional: only if you want repeat runs)
  (cd "$AGENT_DIR" && git checkout -- apps/agent 2>/dev/null || true)

  apply_rebrand "$agent_app"
  copy_icons "$agent_app"

  # Patch codegen to support GRAPHQL_SCHEMA_URL (introspection) so workers repo is not required
  if [[ -f "$REPO_ROOT/scripts/agent-codegen.ts" ]]; then
    cp "$REPO_ROOT/scripts/agent-codegen.ts" "$agent_app/codegen.ts"
    echo "Patched codegen.ts (supports GRAPHQL_SCHEMA_URL for introspection)."
  fi

  cd "$AGENT_DIR"
  echo "Installing deps (bun install) ..."
  bun install

  # .env for agent if needed (codegen may use it)
  if [[ -f "$agent_app/.env.example" ]] && [[ ! -f "$agent_app/.env.development" ]]; then
    cp "$agent_app/.env.example" "$agent_app/.env.development"
  fi

  if [[ -n "${BUILD_AGENT_WITHOUT_CLOUD:-}" ]]; then
    echo "Building extension WITHOUT cloud API (stub generated/graphql, skip codegen) ..."
    mkdir -p "$agent_app/generated/graphql"
    cp -r "$REPO_ROOT/scripts/agent-generated-stub/generated/graphql/"* "$agent_app/generated/graphql"
    # Avoid zod import failing in vite-node during build (use fallback env.ts)
    if [[ -f "$REPO_ROOT/scripts/agent-env-build-fallback.ts" ]]; then
      cp "$REPO_ROOT/scripts/agent-env-build-fallback.ts" "$agent_app/lib/env.ts"
      echo "Patched lib/env.ts (build fallback, no zod)."
    fi
    # Temporarily make "build" skip codegen so "bun run build" only runs wxt (same env as normal build)
    sed -i.bak 's/^    "build": "bun run codegen && wxt build",$/    "build": "wxt build",/' "$agent_app/package.json"
    # Disable source maps to reduce build time/memory (often where it hangs)
    sed -i.bak "s/sourcemap: 'hidden'/sourcemap: false/" "$agent_app/wxt.config.ts"
    trap '[[ -f "$agent_app/wxt.config.ts.bak" ]] && mv "$agent_app/wxt.config.ts.bak" "$agent_app/wxt.config.ts"' EXIT
    # BUILD_EXTENSION_VERBOSE=1 → more Vite/Rollup output (DEBUG=vite:*)
    [[ -n "${BUILD_EXTENSION_VERBOSE:-}" ]] && export DEBUG="${DEBUG:-vite:*}"
    # Line-buffer so progress appears in log when piping to tee (Node buffers when not TTY)
    if [[ -n "${BUILD_EXTENSION_UNBUFFERED:-}" ]] && command -v stdbuf >/dev/null 2>&1; then
      (cd "$agent_app" && stdbuf -oL -eL bun --env-file=.env.development run build)
    else
      (cd "$agent_app" && bun --env-file=.env.development run build)
    fi
    trap - EXIT
    [[ -f "$agent_app/wxt.config.ts.bak" ]] && mv "$agent_app/wxt.config.ts.bak" "$agent_app/wxt.config.ts"
    [[ -f "$agent_app/package.json.bak" ]] && mv "$agent_app/package.json.bak" "$agent_app/package.json"
  else
    echo "Building extension (bun run codegen && wxt build) ..."
    echo "  (Codegen uses GRAPHQL_SCHEMA_URL from .env.development if set, e.g. https://api.browseros.com/graphql; else GRAPHQL_SCHEMA_PATH. No workers repo required.)"
    (cd "$agent_app" && bun run codegen && bun run build)
  fi

  # wxt 0.20+ puts chrome-mv3 in dist/chrome-mv3; older used .output/chrome-mv3
  local out_dir="$agent_app/dist/chrome-mv3"
  if [[ ! -d "$out_dir" ]]; then
    out_dir="$agent_app/dist"
  fi
  if [[ ! -d "$out_dir" ]]; then
    out_dir="$agent_app/.output/chrome-mv3"
  fi
  if [[ ! -d "$out_dir" ]]; then
    out_dir="$agent_app/.output"
    if [[ -d "$out_dir" ]]; then
      out_dir=$(find "$out_dir" -maxdepth 2 -type d -name "*.mv3" 2>/dev/null | head -1)
      [[ -z "$out_dir" ]] && out_dir="$agent_app/.output"
    fi
  fi
  if [[ ! -d "$out_dir" ]]; then
    echo "Build failed: dist or .output not found in $agent_app" >&2
    exit 1
  fi

  mkdir -p "$EXT_DEST"
  rm -rf "$EXT_DEST/agent-build"
  cp -r "$out_dir" "$EXT_DEST/agent-build"
  echo "Done. Unpacked extension copied to $EXT_DEST/agent-build/"
  echo ""
  echo "Next steps:"
  echo "  1) Load unpacked: Chrome -> Extensions -> Load unpacked -> select $EXT_DEST/agent-build"
  echo "  2) To bundle as .crx: Chrome -> Extensions -> Pack extension -> choose $EXT_DEST/agent-build, then put the .crx and bundled_extensions.json in $EXT_DEST (see README there)."
}

main "$@"
