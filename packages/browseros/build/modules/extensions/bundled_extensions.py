#!/usr/bin/env python3
"""Bundled Extensions Module - Use local extensions or download from CDN manifest"""

import json
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, NamedTuple

import requests

from ...common.context import Context
from ...common.module import CommandModule, ValidationError
from ...common.utils import log_info, log_success, log_error, log_warning


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
        output_dir.mkdir(parents=True, exist_ok=True)
        # So patches can add files under chrome/browser/browseros/*, ensure all subdirs exist
        self._ensure_browseros_dirs(ctx)
        log_info(f"  Output: {output_dir}")

        local_dir = ctx.root_dir / "resources" / "extensions"
        if self._use_local_extensions(local_dir, output_dir):
            log_success("Bundled extensions from local resources/extensions/")
            return

        log_info("\n📦 Bundling extensions from CDN manifest...")
        manifest_url = ctx.get_extensions_manifest_url()
        extensions = self._fetch_and_parse_manifest(manifest_url)
        if not extensions:
            raise RuntimeError("No extensions found in manifest")

        log_info(f"  Found {len(extensions)} extensions in manifest")

        for ext in extensions:
            self._download_extension(ext, output_dir)

        self._generate_json(extensions, output_dir)

        log_success(f"Bundled {len(extensions)} extensions successfully")

    def _get_output_dir(self, ctx: Context) -> Path:
        """Get the bundled extensions output directory in Chromium source"""
        return ctx.chromium_src / "chrome" / "browser" / "browseros" / "bundled_extensions"

    def _ensure_browseros_dirs(self, ctx: Context) -> None:
        """Create chrome/browser/browseros/* dirs from chromium_patches so 'new file' patches can apply."""
        patches_dir = ctx.root_dir / "chromium_patches"
        browseros_patches = patches_dir / "chrome" / "browser" / "browseros"
        if not browseros_patches.is_dir():
            return
        base = ctx.chromium_src / "chrome" / "browser" / "browseros"
        for d in browseros_patches.rglob("*"):
            if d.is_dir():
                (base / d.relative_to(browseros_patches)).mkdir(parents=True, exist_ok=True)

    def _use_local_extensions(self, local_dir: Path, output_dir: Path) -> bool:
        """If resources/extensions/ has bundled_extensions.json and .crx files, copy them and return True."""
        if not local_dir.is_dir():
            return False
        json_path = local_dir / "bundled_extensions.json"
        if not json_path.is_file():
            return False
        crx_files = list(local_dir.glob("*.crx"))
        if not crx_files:
            log_warning("  resources/extensions/ has no .crx files; falling back to CDN")
            return False
        log_info("\n📦 Using local extensions from resources/extensions/")
        for f in local_dir.iterdir():
            if f.is_file():
                shutil.copy2(f, output_dir / f.name)
                log_info(f"    Copied {f.name}")
        return True

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
