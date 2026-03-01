#!/usr/bin/env python3
"""Pack agent-build directory to .crx using crx3. Called by pack_agent_crx.sh when npx is not available."""
import sys
from pathlib import Path


def main():
    if len(sys.argv) < 3:
        print(
            "Usage: pack_agent_crx.py <agent_build_dir> <output_crx> [private_key.pem]",
            file=sys.stderr,
        )
        sys.exit(1)
    agent_build = Path(sys.argv[1]).resolve()
    output_crx = Path(sys.argv[2]).resolve()
    key_file = Path(sys.argv[3]).resolve() if len(sys.argv) > 3 else None

    try:
        from crx3 import creator
    except ImportError:
        print(
            "Error: Python package 'crx3' not found. Install it: pip install --user crx3",
            file=sys.stderr,
        )
        sys.exit(1)

    if not agent_build.is_dir():
        print(f"Error: not a directory: {agent_build}", file=sys.stderr)
        sys.exit(1)

    if key_file is not None:
        if not key_file.is_file():
            print(f"Error: key file not found: {key_file}", file=sys.stderr)
            sys.exit(1)
        creator.create_crx_file(str(agent_build), str(key_file), str(output_crx))
    else:
        # No key: create one next to the output (same behavior as crx3 CLI)
        key_path = output_crx.with_suffix(".pem")
        creator.create_private_key_file(str(key_path))
        creator.create_crx_file(str(agent_build), str(key_path), str(output_crx))
        print(f"Created new key: {key_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
