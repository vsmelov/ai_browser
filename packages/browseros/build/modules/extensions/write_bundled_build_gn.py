#!/usr/bin/env python3
"""Write BUILD.gn in bundled_extensions dir from actual files present (so local extensions work)."""

from pathlib import Path

from ...common.context import Context
from ...common.module import CommandModule, ValidationError
from ...common.utils import log_info, log_success


class WriteBundledExtensionsBuildGnModule(CommandModule):
    """After patches: overwrite BUILD.gn in bundled_extensions with list of files actually present."""

    produces = []
    requires = []
    description = "Write BUILD.gn in bundled_extensions from actual files (for local extensions)"

    def validate(self, ctx: Context) -> None:
        if not ctx.chromium_src or not ctx.chromium_src.exists():
            raise ValidationError(f"Chromium source directory not found: {ctx.chromium_src}")

    def execute(self, ctx: Context) -> None:
        output_dir = ctx.chromium_src / "chrome" / "browser" / "browseros" / "bundled_extensions"
        if not output_dir.is_dir():
            log_info("  bundled_extensions dir not found; skipping BUILD.gn write")
            return
        build_gn = output_dir / "BUILD.gn"
        if not build_gn.is_file():
            log_info("  BUILD.gn not found; skipping")
            return
        # List files that should be in sources: bundled_extensions.json + *.crx
        sources = []
        if (output_dir / "bundled_extensions.json").is_file():
            sources.append("bundled_extensions.json")
        for f in sorted(output_dir.glob("*.crx")):
            sources.append(f.name)
        if not sources:
            log_info("  No json/crx in dir; skipping BUILD.gn write")
            return
        body = _build_gn_content(sources)
        build_gn.write_text(body, encoding="utf-8")
        log_success(f"  Wrote BUILD.gn with {len(sources)} source(s)")


def _build_gn_content(sources: list) -> str:
    lines = [
        "# Copyright 2024 The Chromium Authors",
        "# Use of this source code is governed by a BSD-style license that can be",
        "# found in the LICENSE file.",
        "",
        "# Bundled BrowserOS extensions. Sources list synced from files present in this dir.",
        "_bundled_extensions_sources = [",
    ]
    for s in sources:
        lines.append(f'  "{s}",')
    lines.append("]")
    lines.append("")
    lines.append("if (!is_mac) {")
    lines.append('  copy("bundled_extensions") {')
    lines.append("    sources = _bundled_extensions_sources")
    lines.append('    outputs = [ "$root_out_dir/browseros_extensions/{{source_file_part}}" ]')
    lines.append("  }")
    lines.append("} else {")
    lines.append('  bundle_data("bundled_extensions") {')
    lines.append("    sources = _bundled_extensions_sources")
    lines.append('    outputs = [ "{{bundle_contents_dir}}/Resources/browseros_extensions/{{source_file_part}}" ]')
    lines.append("  }")
    lines.append("}")
    lines.append("")
    return "\n".join(lines)
