from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fragrance_cmi.config import META_URL, REVIEW_URL, ProjectPaths  # noqa: E402
from fragrance_cmi.io import download_file, sha256_file  # noqa: E402


def main() -> None:
    paths = ProjectPaths(ROOT)
    paths.ensure_output_dirs()
    assets = {
        "reviews": (REVIEW_URL, paths.raw / "All_Beauty.jsonl.gz"),
        "metadata": (META_URL, paths.raw / "meta_All_Beauty.jsonl.gz"),
    }
    manifest = {}
    for name, (url, destination) in assets.items():
        print(f"Downloading {name}: {url}")
        download_file(url, destination)
        manifest[name] = {
            "url": url,
            "file": destination.name,
            "bytes": destination.stat().st_size,
            "sha256": sha256_file(destination),
        }
    manifest_path = paths.raw / "download_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {manifest_path}")


if __name__ == "__main__":
    main()
