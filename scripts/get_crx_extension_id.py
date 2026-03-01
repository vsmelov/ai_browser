#!/usr/bin/env python3
"""
Get Chrome extension ID and version from a .crx (CRX3) file.
Optionally write bundled_extensions.json so you don't need to look up the ID in Chrome.

Usage:
  python scripts/get_crx_extension_id.py path/to/agent-pack.crx
  python scripts/get_crx_extension_id.py path/to/agent-pack.crx --write-json
"""
import hashlib
import io
import json
import struct
import sys
import zipfile
from pathlib import Path


def chrome_extension_id_from_public_key(key_der: bytes) -> str:
    """Chrome extension ID = first 16 bytes of SHA256(public_key_der), hex digits mapped to a-p."""
    digest = hashlib.sha256(key_der).digest()[:16]
    return "".join(chr(ord("a") + (b >> 4 if i == 0 else b & 0xF)) for b in digest for i in (0, 1))


def _extract_first_pubkey_der(header: bytes) -> bytes:
    i = 0
    while i < len(header) - 4:
        if header[i] == 0x30 and header[i + 1] == 0x82:
            der_len = (header[i + 2] << 8) | header[i + 3]
            if i + 4 + der_len <= len(header):
                return header[i : i + 4 + der_len]
        i += 1
    raise ValueError("No public key in CRX3 header")


def parse_crx3(crx_path: Path) -> tuple[bytes, bytes]:
    raw = crx_path.read_bytes()
    if raw[:4] != b"Cr24":
        raise ValueError("Not CRX3 (magic Cr24 expected)")
    header_len = struct.unpack("<I", raw[8:12])[0]
    zip_start = 12 + header_len
    zip_content = raw[zip_start:]
    if not zip_content.startswith(b"PK"):
        raise ValueError("CRX3: zip payload missing")
    key_der = _extract_first_pubkey_der(raw[12:zip_start])
    return key_der, zip_content


def get_crx_version_and_id(crx_path: Path) -> tuple[str, str]:
    key_der, zip_content = parse_crx3(crx_path)
    ext_id = chrome_extension_id_from_public_key(key_der)
    with zipfile.ZipFile(io.BytesIO(zip_content), "r") as zf:
        manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
    version = manifest.get("version", "")
    return version, ext_id


def main() -> int:
    write_json = "--write-json" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--write-json"]
    if len(args) != 1:
        print(__doc__.strip(), file=sys.stderr)
        sys.exit(1)
    crx_path = Path(args[0]).resolve()
    if not crx_path.is_file():
        print(f"Error: not a file: {crx_path}", file=sys.stderr)
        sys.exit(1)
    try:
        version, ext_id = get_crx_version_and_id(crx_path)
    except Exception as e:
        print(f"Error reading .crx: {e}", file=sys.stderr)
        sys.exit(1)
    crx_name = crx_path.name
    print(f"Extension ID: {ext_id}")
    print(f"Version:      {version}")
    print(f"CRX file:     {crx_name}")
    if write_json:
        out_path = crx_path.parent / "bundled_extensions.json"
        data = {
            ext_id: {
                "external_crx": crx_name,
                "external_version": version,
            }
        }
        out_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote:        {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
