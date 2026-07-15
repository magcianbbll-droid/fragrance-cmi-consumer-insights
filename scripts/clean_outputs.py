from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fragrance_cmi.config import ProjectPaths  # noqa: E402
from fragrance_cmi.io import remove_tree_contents  # noqa: E402


def main() -> None:
    paths = ProjectPaths(ROOT)
    for target in (paths.processed, paths.figures, paths.tables):
        remove_tree_contents(target)
        print(f"Cleaned {target}")


if __name__ == "__main__":
    main()
