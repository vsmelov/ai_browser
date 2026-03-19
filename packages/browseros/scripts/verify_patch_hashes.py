#!/usr/bin/env python3
"""Generate or verify SHA256 hashes of patched files in Chromium tree.

After applying patches, run --generate to save current hashes. Later run
--verify to ensure a fresh apply produced the same files (1:1).

  uv run python scripts/verify_patch_hashes.py --chromium-src /path/to/chromium/src --generate
  uv run python scripts/verify_patch_hashes.py --chromium-src /path/to/chromium/src --verify

Manifest is saved in chromium_patches/patch_result_hashes.json (relative to repo root).
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Optional


def repo_root() -> Path:
    root = Path(__file__).resolve().parent.parent
    assert (root / "chromium_patches").exists(), "Run from browseros package"
    return root


def get_patch_target_paths(patches_dir: Path, exclude_manifest: Optional[Path] = None) -> list[str]:
    """List relative paths of all files under patches_dir (mirrors Chromium src layout)."""
    paths = []
    exclude_resolved = exclude_manifest.resolve() if exclude_manifest else None
    for f in sorted(patches_dir.rglob("*")):
        if not f.is_file():
            continue
        if f.suffix in (".deleted", ".binary", ".rename") or f.name.startswith("."):
            continue
        if exclude_resolved and f.resolve() == exclude_resolved:
            continue
        try:
            rel = f.relative_to(patches_dir)
        except ValueError:
            continue
        paths.append(str(rel).replace("\\", "/"))
    return sorted(paths)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def run_generate(chromium_src: Path, patches_dir: Path, manifest_path: Path) -> int:
    paths = get_patch_target_paths(patches_dir, exclude_manifest=manifest_path)
    manifest = {}
    for rel in paths:
        full = chromium_src / rel
        if not full.exists():
            print(f"  skip (missing): {rel}", file=sys.stderr)
            continue
        manifest[rel] = sha256_file(full)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(manifest)} hashes to {manifest_path}")
    return 0


def run_verify(chromium_src: Path, manifest_path: Path) -> int:
    if not manifest_path.exists():
        print(f"Manifest not found: {manifest_path}", file=sys.stderr)
        print("Run with --generate first after a known-good patch apply.", file=sys.stderr)
        return 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    failed = []
    for rel, expected in manifest.items():
        full = chromium_src / rel
        if not full.exists():
            failed.append((rel, "missing"))
            continue
        actual = sha256_file(full)
        if actual != expected:
            failed.append((rel, f"hash mismatch (expected {expected[:16]}..., got {actual[:16]}...)"))
    if failed:
        print("Verify FAILED:", file=sys.stderr)
        for rel, msg in failed:
            print(f"  {rel}: {msg}", file=sys.stderr)
        return 1
    print(f"Verify OK: {len(manifest)} files match manifest.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().split("\n\n")[0])
    ap.add_argument("--chromium-src", "-S", required=True, type=Path, help="Path to Chromium src/")
    ap.add_argument("--generate", action="store_true", help="Generate manifest from current tree")
    ap.add_argument("--verify", action="store_true", help="Verify tree hashes against manifest")
    ap.add_argument("--manifest", type=Path, default=None, help="Manifest path (default: chromium_patches/patch_result_hashes.json)")
    args = ap.parse_args()
    root = repo_root()
    patches_dir = root / "chromium_patches"
    manifest_path = args.manifest or (root / "chromium_patches" / "patch_result_hashes.json")

    if args.generate:
        return run_generate(args.chromium_src, patches_dir, manifest_path)
    if args.verify:
        return run_verify(args.chromium_src, manifest_path)
    ap.error("Use --generate or --verify")
    return 1


if __name__ == "__main__":
    sys.exit(main())
