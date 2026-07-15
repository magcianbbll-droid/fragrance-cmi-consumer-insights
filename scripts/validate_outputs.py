from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fragrance_cmi.config import ProjectPaths  # noqa: E402
from fragrance_cmi.io import write_json  # noqa: E402


def main() -> None:
    paths = ProjectPaths(ROOT)
    reviews_file = paths.processed / "reviews_tagged_no_text.csv"
    if not reviews_file.exists():
        raise FileNotFoundError("Run scripts/run_pipeline.py before validation.")

    reviews = pd.read_csv(reviews_file, low_memory=False)
    summary = json.loads((paths.tables / "summary_metrics.json").read_text(encoding="utf-8"))
    quality = json.loads((paths.tables / "data_quality_summary.json").read_text(encoding="utf-8"))
    pain = pd.read_csv(paths.tables / "pain_points.csv")
    price = pd.read_csv(paths.tables / "price_bands.csv")
    repurchase = pd.read_csv(paths.tables / "repurchase_intent.csv")

    checks: dict[str, dict[str, object]] = {}

    def check(name: str, actual: object, expected: object) -> None:
        passed = actual == expected
        checks[name] = {"passed": passed, "actual": actual, "expected": expected}
        if not passed:
            raise AssertionError(f"{name}: actual={actual!r}, expected={expected!r}")

    check("analysis_row_count", len(reviews), summary["analysis_review_rows"])
    check("review_key_unique", int(reviews["review_key"].nunique()), len(reviews))
    check(
        "matched_minus_duplicates",
        quality["matched_review_rows"] - quality.get("duplicate_review_rows", 0),
        len(reviews),
    )
    eligible = reviews["text_eligible"].astype(bool) & ~reviews["pure_promo_noise"].astype(bool)
    check("text_eligible_rows", int(eligible.sum()), summary["text_eligible_rows"])
    negative = reviews["sentiment"].eq("negative")
    check("negative_rows", int(negative.sum()), summary["negative_review_rows"])
    check(
        "negative_text_denominator",
        int((eligible & negative).sum()),
        summary["negative_text_eligible_rows"],
    )
    check("priced_rows", int(reviews["price_usd"].notna().sum()), int(price["review_volume"].sum()))
    explicit = int(
        repurchase.loc[repurchase["repurchase_intent"].isin(["positive", "negative"]), "review_volume"].sum()
    )
    check("explicit_repurchase_rows", explicit, summary["explicit_repurchase_rows"])
    check("top_pain_label", str(pain.iloc[0]["category"]), summary["top_pain_point"])

    top_three_share = float(pain.head(3)["share_of_tag_mentions"].sum())
    check("top_three_pain_share_round_4", round(top_three_share, 4), 0.7013)

    forbidden_columns = {"text", "title", "user_id"}.intersection(reviews.columns)
    check("forbidden_raw_columns", sorted(forbidden_columns), [])

    workbook_path = paths.root / "outputs" / "fragrance_cmi_weekly_tracker.xlsx"
    with zipfile.ZipFile(workbook_path) as archive:
        bad_member = archive.testzip()
        sheet_files = [name for name in archive.namelist() if name.startswith("xl/worksheets/sheet")]
    check("xlsx_zip_integrity", bad_member, None)
    check("xlsx_sheet_count", len(sheet_files), 13)

    figure_files = sorted(paths.figures.glob("*.png"))
    check("figure_count", len(figure_files), 9)
    check("nonempty_figures", all(file.stat().st_size > 10_000 for file in figure_files), True)

    receipt = {
        "status": "passed",
        "checks_passed": len(checks),
        "analysis_rows": len(reviews),
        "top_three_pain_tag_share": top_three_share,
        "checks": checks,
    }
    write_json(receipt, paths.tables / "validation_receipt.json")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
