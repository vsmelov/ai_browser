#!/usr/bin/env python3
"""
Verify that all chromium_patches are fully applied in the chromium tree.

For each patch file:
  1. Get the "clean" file from chromium git at --ref (e.g. tag from CHROMIUM_VERSION).
  2. Apply our patch in a temp dir the same way the build does: plain apply, then
     --3way if the first attempt fails.
  3. Compare the result with the file currently in chromium_src.

If they match, the tree is consistent with "clean ref + our patches". If not, we
report a mismatch.

Usage:
  python scripts/verify_patches_applied.py --chromium-src /path/to/chromium/src \\
      [--ref TAG] [--patches-dir packages/browseros/chromium_patches]

Requires: git. Default --ref is from CHROMIUM_VERSION (e.g. 145.0.7632.45).
"""

import argparse
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------

def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def log(msg: str) -> None:
    logging.info(msg)


def log_ok(msg: str) -> None:
    logging.info("  ✓ %s", msg)


def log_fail(msg: str) -> None:
    logging.error("  ✗ %s", msg)


def log_skip(msg: str) -> None:
    logging.warning("  ⏭ %s", msg)


def log_debug(msg: str) -> None:
    logging.debug("  %s", msg)


# -----------------------------------------------------------------------------
# Patch discovery (same rules as build/modules/apply/common.py)
# -----------------------------------------------------------------------------

def find_patch_files(patches_dir: Path) -> list[Path]:
    if not patches_dir.exists():
        return []
    return sorted(
        p
        for p in patches_dir.rglob("*")
        if p.is_file()
        and not p.name.endswith(".deleted")
        and not p.name.endswith(".binary")
        and not p.name.endswith(".rename")
        and p.name != "patch_result_hashes.json"
        and not p.name.startswith(".")
    )


def get_target_path(patch_path: Path, patches_dir: Path) -> str:
    """Return chromium-relative path for this patch (e.g. chrome/browser/ui/foo.cc)."""
    return str(patch_path.relative_to(patches_dir)).replace("\\", "/")


# -----------------------------------------------------------------------------
# Git helpers
# -----------------------------------------------------------------------------

def run_git(cwd: Path, *args: str, capture: bool = True) -> subprocess.CompletedProcess:
    cmd = ["git"] + list(args)
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=capture,
        text=True,
        timeout=120,
    )


def file_exists_at_ref(chromium_src: Path, ref: str, path: str) -> bool:
    r = run_git(chromium_src, "cat-file", "-e", f"{ref}:{path}")
    return r.returncode == 0


def get_file_at_ref(chromium_src: Path, ref: str, path: str) -> bytes | None:
    r = run_git(chromium_src, "show", f"{ref}:{path}")
    if r.returncode != 0:
        return None
    return r.stdout.encode("utf-8") if isinstance(r.stdout, str) else r.stdout


# -----------------------------------------------------------------------------
# Apply patch in temp dir and return resulting file content
# Same strategy as build: try plain apply, then --3way (so verification matches reality).
# -----------------------------------------------------------------------------

def _apply_once(work_dir: Path, patch_path: Path, use_3way: bool) -> subprocess.CompletedProcess:
    args = [
        "apply",
        "--ignore-whitespace",
        "--whitespace=nowarn",
        "-p1",
    ]
    if use_3way:
        args.append("--3way")
    args.append(str(patch_path))
    return run_git(work_dir, *args)


def apply_patch_to_clean_content(
    patch_path: Path,
    clean_content: bytes | None,
    target_path: str,
    work_dir: Path,
) -> tuple[bool, bytes | None]:
    """
    Write clean_content to work_dir/target_path (or nothing for new files),
    apply patch like the build does: first plain apply, then --3way if needed.
    Then read work_dir/target_path.

    Returns (success, content_after_apply).
    """
    work_file = work_dir / target_path
    work_file.parent.mkdir(parents=True, exist_ok=True)

    if clean_content is not None:
        work_file.write_bytes(clean_content)
    elif work_file.exists():
        work_file.unlink()

    r = _apply_once(work_dir, patch_path, use_3way=False)
    if r.returncode != 0:
        # Fallback: 3-way (same as build). Need a git repo so --3way can resolve.
        run_git(work_dir, "init", "-q")
        run_git(work_dir, "add", "-A")
        run_git(work_dir, "config", "user.email", "verify@local")
        run_git(work_dir, "config", "user.name", "Verify")
        run_git(work_dir, "commit", "-m", "base", "--allow-empty")
        r = _apply_once(work_dir, patch_path, use_3way=True)
    if r.returncode != 0:
        return False, None

    if not work_file.exists():
        return False, None
    return True, work_file.read_bytes()


# -----------------------------------------------------------------------------
# Compare and report
# -----------------------------------------------------------------------------

def normalize_for_compare(data: bytes) -> bytes:
    """Normalize line endings to LF for comparison."""
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def patch_already_applied_in_tree(chromium_src: Path, patch_path: Path) -> bool:
    """True if the patch is already applied (reverse apply would succeed)."""
    r = run_git(
        chromium_src,
        "apply", "--check", "--reverse",
        "--ignore-whitespace", "--whitespace=nowarn",
        "-p1", str(patch_path),
    )
    return r.returncode == 0


def verify_one(
    patch_path: Path,
    patches_dir: Path,
    chromium_src: Path,
    ref: str,
    work_dir: Path,
) -> tuple[bool, str]:
    """
    Verify a single patch. Returns (ok, message).
    """
    target_path = get_target_path(patch_path, patches_dir)
    chromium_file = chromium_src / target_path

    if not chromium_file.exists():
        return False, f"target missing in chromium: {target_path}"

    log_debug(f"verify {target_path} (ref={ref})")

    clean = get_file_at_ref(chromium_src, ref, target_path)
    if clean is None:
        log_debug(f"  no file at ref (treat as new file)")

    ok, content_after = apply_patch_to_clean_content(
        patch_path, clean, target_path, work_dir
    )
    if not ok or content_after is None:
        # Temp apply failed (e.g. patch context doesn't match ref, or multi-file).
        # If in the real tree the patch is already applied, we're still consistent.
        if patch_already_applied_in_tree(chromium_src, patch_path):
            return True, "already applied (reverse check)"
        return False, "failed to apply patch in temp dir (base may have changed)"

    current = chromium_file.read_bytes()
    if normalize_for_compare(content_after) == normalize_for_compare(current):
        return True, "match"
    return False, "content differs from expected (patch result)"


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Verify that chromium_patches are fully applied in chromium tree."
    )
    ap.add_argument(
        "--chromium-src",
        type=Path,
        required=True,
        help="Path to chromium source tree (git repo)",
    )
    ap.add_argument(
        "--ref",
        default=None,
        help="Git ref for 'clean' base (tag like 145.0.7632.45, or origin/main). Default: from CHROMIUM_VERSION.",
    )
    ap.add_argument(
        "--patches-dir",
        type=Path,
        default=None,
        help="Path to chromium_patches (default: packages/browseros/chromium_patches relative to script)",
    )
    ap.add_argument(
        "--chromium-version-file",
        type=Path,
        default=None,
        help="CHROMIUM_VERSION file (default: packages/browseros/CHROMIUM_VERSION relative to script)",
    )
    ap.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose (debug) logging",
    )
    args = ap.parse_args()

    setup_logging(args.verbose)

    chromium_src = args.chromium_src.resolve()
    if not (chromium_src / ".git").exists():
        log_fail("chromium_src is not a git repo")
        return 1

    if args.patches_dir is not None:
        patches_dir = args.patches_dir.resolve()
    else:
        # Default: same repo as script -> packages/browseros/chromium_patches
        script_dir = Path(__file__).resolve().parent
        patches_dir = script_dir.parent / "chromium_patches"
    if not patches_dir.exists():
        log_fail(f"patches_dir not found: {patches_dir}")
        return 1

    ref = args.ref
    if not ref:
        script_dir = Path(__file__).resolve().parent
        version_file = args.chromium_version_file or (script_dir.parent / "CHROMIUM_VERSION")
        if version_file.exists():
            vs = {}
            for line in version_file.read_text().splitlines():
                line = line.strip()
                if "=" in line:
                    k, v = line.split("=", 1)
                    vs[k.strip()] = v.strip()
            if "MAJOR" in vs and "MINOR" in vs and "BUILD" in vs and "PATCH" in vs:
                ref = f"{vs['MAJOR']}.{vs['MINOR']}.{vs['BUILD']}.{vs['PATCH']}"
                log(f"Using ref from CHROMIUM_VERSION: {ref}")
        if not ref:
            ref = "HEAD"
            log("No --ref and no CHROMIUM_VERSION; using HEAD (may give false positives)")

    log("Options:")
    log(f"  chromium_src = {chromium_src}")
    log(f"  patches_dir  = {patches_dir}")
    log(f"  ref          = {ref}")
    log("")

    patch_files = find_patch_files(patches_dir)
    log(f"Found {len(patch_files)} patch files")
    if not patch_files:
        log_skip("Nothing to verify")
        return 0

    ok_count = 0
    fail_list: list[tuple[str, str]] = []

    for i, patch_path in enumerate(patch_files, 1):
        rel = patch_path.relative_to(patches_dir)
        log(f"[{i}/{len(patch_files)}] {rel}")
        with tempfile.TemporaryDirectory(prefix="verify_patch_") as work_dir:
            work_path = Path(work_dir)
            ok, msg = verify_one(
                patch_path, patches_dir, chromium_src, ref, work_path
            )
        if ok:
            log_ok(msg)
            ok_count += 1
        else:
            log_fail(msg)
            fail_list.append((str(rel), msg))

    log("")
    log("Summary:")
    log(f"  OK:   {ok_count}/{len(patch_files)}")
    log(f"  FAIL: {len(fail_list)}")
    if fail_list:
        log("Failed:")
        for rel, msg in fail_list:
            log(f"  - {rel}: {msg}")
        log("")
        log("Note: Verification uses the same apply strategy as the build (plain apply, then --3way).")
        log("FAIL here means we could not reproduce the patched file in a temp dir (context mismatch or multi-file).")
        log("If a full 'browseros build --setup --prep' has succeeded, the tree is likely consistent.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
