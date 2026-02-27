#!/usr/bin/env python3
"""Clean module for BrowserOS build system"""

import os
import tempfile

from ...common.module import CommandModule, ValidationError
from ...common.context import Context
from ...common.utils import run_command, log_info, log_success, log_warning, safe_rmtree


class CleanModule(CommandModule):
    produces = []
    requires = []
    description = "Clean build artifacts and reset git state"

    def validate(self, ctx: Context) -> None:
        if not ctx.chromium_src.exists():
            raise ValidationError(f"Chromium source not found: {ctx.chromium_src}")

    def execute(self, ctx: Context) -> None:
        log_info("🧹 Cleaning build artifacts...")

        out_path = ctx.chromium_src / ctx.out_dir
        if out_path.exists():
            safe_rmtree(out_path)
            log_success("Cleaned build directory")

        log_info("\n🔀 Resetting git branch and removing tracked files...")
        self._git_reset(ctx)

        log_info("\n🧹 Cleaning Sparkle build artifacts...")
        self._clean_sparkle(ctx)

    def _clean_sparkle(self, ctx: Context) -> None:
        sparkle_dir = ctx.get_sparkle_dir()
        if sparkle_dir.exists():
            safe_rmtree(sparkle_dir)
        log_success("Cleaned Sparkle build directory")

    def _git_reset(self, ctx: Context) -> None:
        # Use a temp index on local disk (e.g. /tmp) to avoid "Could not write new index file"
        # when the repo is on NFS or a slow/shared filesystem.
        import shutil

        fd, index_tmp = tempfile.mkstemp(prefix="chromium-index-", suffix=".git-index")
        os.close(fd)
        git_index = ctx.chromium_src / ".git" / "index"
        if git_index.exists():
            shutil.copy2(git_index, index_tmp)
        env = os.environ.copy()
        env["GIT_INDEX_FILE"] = index_tmp
        if os.environ.get("CLEAN_GIT_VERBOSE"):
            env["GIT_TRACE"] = "1"
            env["GIT_TRACE_PACKET"] = "1"
            log_info("  (CLEAN_GIT_VERBOSE=1: git trace enabled)")
        try:
            run_command(["git", "reset", "--hard", "HEAD"], cwd=ctx.chromium_src, env=env)

            log_info("🧹 Running git clean with exclusions...")
            run_command(
                [
                    "git",
                    "clean",
                    "-fdx",
                    "chrome/",
                    "components/",
                    "--exclude=third_party/",
                    "--exclude=build_tools/",
                    "--exclude=uc_staging/",
                    "--exclude=buildtools/",
                    "--exclude=tools/",
                    "--exclude=build/",
                ],
                cwd=ctx.chromium_src,
                env=env,
            )
            # Copy temp index back so .git/index is consistent (needed for later git operations).
            try:
                shutil.copy2(index_tmp, git_index)
            except OSError as e:
                log_warning(f"  Could not copy index to .git/index: {e}")
                log_warning("  Repo may still work; if patches fail, try running from local disk.")
            log_success("Git reset and clean complete")
        finally:
            try:
                os.unlink(index_tmp)
            except OSError:
                pass
