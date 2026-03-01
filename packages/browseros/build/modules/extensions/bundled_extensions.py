#!/usr/bin/env python3
"""Bundled Extensions Module - Download and bundle extensions from CDN manifest"""

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, NamedTuple

import requests

from ...common.context import Context
from ...common.module import CommandModule, ValidationError
from ...common.utils import log_info, log_success, log_error


class ExtensionInfo(NamedTuple):
    """Extension metadata parsed from update manifest"""
    id: str
    version: str
    codebase: str


class BundledExtensionsModule(CommandModule):
    """Download extensions from CDN manifest and create bundled_extensions.json"""

    produces = ["bundled_extensions"]
    requires = []
    description = "Download and bundle extensions from CDN update manifest"

    def validate(self, ctx: Context) -> None:
        if not ctx.chromium_src or not ctx.chromium_src.exists():
            raise ValidationError(
                f"Chromium source directory not found: {ctx.chromium_src}"
            )

    def execute(self, ctx: Context) -> None:
        output_dir = self._get_output_dir(ctx)
        local_ext_dir = ctx.root_dir / "resources" / "extensions"

        # If local bundled_extensions.json and .crx files exist, use them instead of CDN
        local_json = local_ext_dir / "bundled_extensions.json"
        if local_json.exists():
            if self._use_local_extensions(local_ext_dir, output_dir, local_json):
                return

        log_info("\n📦 Bundling extensions from CDN manifest...")

        manifest_url = ctx.get_extensions_manifest_url()
        output_dir.mkdir(parents=True, exist_ok=True)
        log_info(f"  Output: {output_dir}")

        extensions = self._fetch_and_parse_manifest(manifest_url)
        if not extensions:
            raise RuntimeError("No extensions found in manifest")

        log_info(f"  Found {len(extensions)} extensions in manifest")

        for ext in extensions:
            self._download_extension(ext, output_dir)

        self._generate_json(extensions, output_dir)
        self._write_sources_gni(
            output_dir,
            ["bundled_extensions.json"] + [f"{ext.id}.crx" for ext in extensions],
        )

        log_success(f"Bundled {len(extensions)} extensions successfully")

    def _use_local_extensions(
        self, local_ext_dir: Path, output_dir: Path, local_json: Path
    ) -> bool:
        """Use local bundled_extensions.json and .crx from resources/extensions. Returns True if used."""
        import shutil

        try:
            with open(local_json) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            log_error(f"  Failed to read local {local_json.name}: {e}")
            return False

        if not data or not isinstance(data, dict):
            log_error("  Local bundled_extensions.json is empty or invalid")
            return False

        missing = []
        for ext_id, entry in data.items():
            if not isinstance(entry, dict):
                continue
            crx_name = entry.get("external_crx")
            if not crx_name:
                continue
            crx_path = local_ext_dir / crx_name
            if not crx_path.exists():
                missing.append(crx_name)

        if missing:
            log_error(f"  Local extensions missing .crx: {missing}")
            return False

        log_info("\n📦 Using local extensions from resources/extensions/...")
        output_dir.mkdir(parents=True, exist_ok=True)
        log_info(f"  Output: {output_dir}")

        # In tree we always use filenames by extension ID ({id}.crx), same as CDN path
        normalized: Dict[str, Dict[str, str]] = {}
        source_files: List[str] = ["bundled_extensions.json"]
        for ext_id, entry in data.items():
            if not isinstance(entry, dict):
                continue
            crx_name = entry.get("external_crx")
            if not crx_name:
                continue
            dest_name = f"{ext_id}.crx"
            shutil.copy2(local_ext_dir / crx_name, output_dir / dest_name)
            normalized[ext_id] = {
                "external_crx": dest_name,
                "external_version": entry.get("external_version", ""),
            }
            source_files.append(dest_name)
            log_info(f"  Copied {crx_name} -> {dest_name}")

        (output_dir / "bundled_extensions.json").write_text(
            json.dumps(normalized, indent=2) + "\n", encoding="utf-8"
        )
        self._write_sources_gni(output_dir, source_files)
        log_success("Bundled local extensions successfully")
        return True

    def _write_sources_gni(self, output_dir: Path, source_files: List[str]) -> None:
        """Write sources.gni so BUILD.gn copies exactly the files we produced."""
        lines = ["bundled_extensions_sources = ["]
        for i, name in enumerate(source_files):
            lines.append(f'  "{name}"' + ("," if i < len(source_files) - 1 else ""))
        lines.append("]")
        gni_path = output_dir / "sources.gni"
        gni_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        log_info(f"  Wrote {gni_path.name}")

    def _get_output_dir(self, ctx: Context) -> Path:
        """Get the bundled extensions output directory in Chromium source"""
        return ctx.chromium_src / "chrome" / "browser" / "browseros" / "bundled_extensions"

    def _fetch_and_parse_manifest(self, url: str) -> List[ExtensionInfo]:
        """Fetch XML manifest and parse extension information"""
        log_info(f"  Fetching manifest: {url}")

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch manifest: {e}")

        return self._parse_manifest_xml(response.text)

    def _parse_manifest_xml(self, xml_content: str) -> List[ExtensionInfo]:
        """Parse Google Update protocol XML manifest

        Expected format (with namespace):
        <gupdate xmlns="http://www.google.com/update2/response" protocol='2.0'>
          <app appid='extension_id'>
            <updatecheck codebase='https://...' version='1.0.0' />
          </app>
        </gupdate>
        """
        extensions = []

        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            raise RuntimeError(f"Failed to parse manifest XML: {e}")

        ns = {"gupdate": "http://www.google.com/update2/response"}

        # Try with namespace first, then without (for flexibility)
        apps = root.findall(".//gupdate:app", ns)
        if not apps:
            apps = root.findall(".//app")

        for app in apps:
            app_id = app.get("appid")
            if not app_id:
                continue

            updatecheck = app.find("gupdate:updatecheck", ns)
            if updatecheck is None:
                updatecheck = app.find("updatecheck")
            if updatecheck is None:
                continue

            version = updatecheck.get("version")
            codebase = updatecheck.get("codebase")

            if version and codebase:
                extensions.append(ExtensionInfo(
                    id=app_id,
                    version=version,
                    codebase=codebase,
                ))

        return extensions

    def _download_extension(self, ext: ExtensionInfo, output_dir: Path) -> None:
        """Download a single extension .crx file"""
        dest_filename = f"{ext.id}.crx"
        dest_path = output_dir / dest_filename

        log_info(f"  Downloading {ext.id} v{ext.version}...")

        try:
            response = requests.get(ext.codebase, stream=True, timeout=60)
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0

            with open(dest_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=65536):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        percent = (downloaded / total_size * 100)
                        sys.stdout.write(
                            f"\r    {dest_filename}: {percent:.0f}%  "
                        )
                        sys.stdout.flush()

            if total_size:
                sys.stdout.write(f"\r    {dest_filename}: done ({total_size / 1024:.0f} KB)\n")
            else:
                sys.stdout.write(f"\r    {dest_filename}: done\n")
            sys.stdout.flush()

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to download {ext.id}: {e}")

    def _generate_json(self, extensions: List[ExtensionInfo], output_dir: Path) -> None:
        """Generate bundled_extensions.json"""
        json_path = output_dir / "bundled_extensions.json"

        data: Dict[str, Dict[str, str]] = {}
        for ext in extensions:
            data[ext.id] = {
                "external_crx": f"{ext.id}.crx",
                "external_version": ext.version,
            }

        with open(json_path, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")

        log_info(f"  Generated {json_path.name}")
