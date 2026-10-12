"""Build only the three isolated ZIPs for publication on GitHub Releases.

Run from the repository root: python -m tools.build_public_bundles
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from lab.exports import export_zip
from lab.store import VERSION_DIRS


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("dist/public-bundles"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for version in VERSION_DIRS:
        content = export_zip(version)
        path = args.output / f"laboratorio_{version}_chatgpt.zip"
        path.write_bytes(content)
        print(
            f"{path}: {len(content)} bytes; SHA256 {hashlib.sha256(content).hexdigest()}"
        )


if __name__ == "__main__":
    main()
