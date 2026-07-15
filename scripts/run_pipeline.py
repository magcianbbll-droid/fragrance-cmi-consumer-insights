from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fragrance_cmi.analysis import run_analysis  # noqa: E402
from fragrance_cmi.config import ProjectPaths  # noqa: E402
from fragrance_cmi.pipeline import run_cleaning  # noqa: E402
from fragrance_cmi.report import build_report  # noqa: E402
from fragrance_cmi.visualize import build_all_figures  # noqa: E402


def main() -> None:
    paths = ProjectPaths(ROOT)
    print("[1/4] Cleaning and tagging real review data")
    products, reviews, quality = run_cleaning(paths)
    print(f"      {len(products):,} fragrance products; {len(reviews):,} reviews")
    print("[2/4] Building analysis tables")
    tables = run_analysis(paths, products, reviews, quality)
    print("[3/4] Rendering figures")
    build_all_figures(paths, tables)
    print("[4/4] Writing the decision-oriented insight report")
    report_path = build_report(paths, quality, tables)
    print(f"Done: {report_path}")


if __name__ == "__main__":
    main()
