#!/usr/bin/env python3
"""
Verify built extension has expected ID and version from bundled_extensions.json.
Reads expected values from bundled_extensions.json, checks manifest.json (unpacked)
and optionally the .crx file (packed) for version and ID.

Usage:
  python scripts/verify_extension_bundle.py --bundled-json path/to/bundled_extensions.json --manifest path/to/agent-build/manifest.json
  python scripts/verify_extension_bundle.py --bundled-json path --manifest path --crx path/to/id.crx
"""

import argparse
import hashlib
import io
import json
import struct
import sys
import zipfile
from pathlib import Path


def load_bundled_expectations(bundled_json_path: Path) -> list[tuple[str, str, str]]:
    """Load (extension_id, external_crx, external_version) from bundled_extensions.json."""
    data = json.loads(bundled_json_path.read_text())
    out = []
    for ext_id, cfg in data.items():
        if isinstance(cfg, dict):
            crx = cfg.get("external_crx", "")
            ver = cfg.get("external_version", "")
            out.append((ext_id, crx, ver))
    return out


def get_manifest_version(manifest_path: Path) -> str:
    """Read version from manifest.json."""
    data = json.loads(manifest_path.read_text())
    return data.get("version", "")


def chrome_extension_id_from_public_key(key_der: bytes) -> str:
    """Compute Chrome extension ID from public key DER (first 16 bytes of SHA256, a-p encoding)."""
    digest = hashlib.sha256(key_der).digest()[:16]
    result = []
    for b in digest:
        for nibble in (b >> 4, b & 0xF):
            result.append(chr(ord("a") + nibble))
    return "".join(result)


def parse_crx3(crx_path: Path) -> tuple[bytes, bytes]:
    """Parse CRX3 file: return (public_key_der, zip_content)."""
    raw = crx_path.read_bytes()
    if raw[:4] != b"Cr24":
        raise ValueError("Not a CRX3 file (magic mismatch)")
    header_len = struct.unpack("<I", raw[8:12])[0]
    zip_start = 12 + header_len
    zip_content = raw[zip_start:]
    if not zip_content.startswith(b"PK"):
        raise ValueError("CRX3: zip payload does not start with PK")
    header = raw[12:zip_start]
    key_der = _extract_first_pubkey_der(header)
    return key_der, zip_content


def _extract_first_pubkey_der(header: bytes) -> bytes:
    """Extract first X.509 SubjectPublicKeyInfo (DER) from CRX3 protobuf header."""
    i = 0
    while i < len(header) - 4:
        if header[i] == 0x30 and header[i + 1] == 0x82:
            len_high, len_low = header[i + 2], header[i + 3]
            der_len = (len_high << 8) | len_low
            total = 4 + der_len
            if i + total <= len(header):
                return header[i : i + total]
        i += 1
    raise ValueError("No public key found in CRX3 header")


def get_crx_version_and_id(crx_path: Path) -> tuple[str, str]:
    """Read version from manifest inside CRX and compute extension ID from CRX3 key."""
    key_der, zip_content = parse_crx3(crx_path)
    ext_id = chrome_extension_id_from_public_key(key_der)
    with zipfile.ZipFile(io.BytesIO(zip_content), "r") as zf:
        manifest_bytes = zf.read("manifest.json")
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    version = manifest.get("version", "")
    return version, ext_id


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify extension ID and version")
    ap.add_argument("--bundled-json", type=Path, required=True, help="bundled_extensions.json path")
    ap.add_argument("--manifest", type=Path, default=None, help="Unpacked manifest.json (e.g. agent-build/manifest.json)")
    ap.add_argument("--crx", type=Path, default=None, help="Packed .crx file to verify")
    args = ap.parse_args()

    bundled_path = args.bundled_json
    if not bundled_path.is_file():
        print(f"Error: bundled_extensions.json not found: {bundled_path}", file=sys.stderr)
        return 1

    expectations = load_bundled_expectations(bundled_path)
    if not expectations:
        print("Error: no entries in bundled_extensions.json", file=sys.stderr)
        return 1

    expected_id, expected_crx_name, expected_version = expectations[0]
    errors = []

    if args.manifest and args.manifest.is_file():
        got_version = get_manifest_version(args.manifest)
        if got_version != expected_version:
            errors.append(f"Manifest version mismatch: expected {expected_version!r}, got {got_version!r} (in {args.manifest})")
        else:
            print(f"  Version in manifest.json: {got_version} (expected {expected_version})")

    if args.crx and args.crx.is_file():
        try:
            crx_version, crx_id = get_crx_version_and_id(args.crx)
            if crx_version != expected_version:
                errors.append(f"CRX version mismatch: expected {expected_version!r}, got {crx_version!r} (in {args.crx})")
            else:
                print(f"  Version in .crx: {crx_version} (expected {expected_version})")
            if crx_id != expected_id:
                errors.append(f"CRX extension ID mismatch: expected {expected_id!r}, got {crx_id!r} (file {args.crx})")
            else:
                print(f"  Extension ID in .crx: {crx_id} (expected {expected_id})")
        except Exception as e:
            errors.append(f"Failed to read .crx: {e}")

    if errors:
        for e in errors:
            print(f"Error: {e}", file=sys.stderr)
        return 1
    print("  Extension ID and version OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
