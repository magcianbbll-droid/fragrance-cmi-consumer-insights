import gzip
import json
from pathlib import Path

import pandas as pd

from fragrance_cmi.config import load_taxonomy
from fragrance_cmi.pipeline import extract_tagged_reviews


def _write_reviews(path: Path, rows: list[dict]) -> None:
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


RUNTIME = Path(__file__).resolve().parent / "fixtures" / "runtime"


def test_review_extraction_deduplicates_and_drops_raw_text() -> None:
    taxonomy = load_taxonomy(Path(__file__).resolve().parents[1] / "configs" / "taxonomy.json")
    products = pd.DataFrame(
        [
            {
                "parent_asin": "P1",
                "product_title": "Example Eau de Parfum",
                "brand": "Example",
                "price_usd": 49.0,
                "product_format": "eau_de_parfum",
                "product_average_rating": 4.2,
                "product_rating_count": 100,
            }
        ]
    )
    review = {
        "rating": 1.0,
        "title": "Not worth it",
        "text": "Too expensive and it does not last. I will not buy again.",
        "parent_asin": "P1",
        "user_id": "RAW-USER-ID",
        "timestamp": 1_690_848_000_000,
        "helpful_vote": 2,
        "verified_purchase": True,
    }
    source = RUNTIME / "dedupe_reviews.jsonl.gz"
    _write_reviews(source, [review, review])

    frame, stats = extract_tagged_reviews(source, products, taxonomy)

    assert len(frame) == 1
    assert stats["matched_review_rows"] == 2
    assert stats["duplicate_review_rows"] == 1
    assert frame.loc[0, "pain_longevity"]
    assert frame.loc[0, "pain_value"]
    assert frame.loc[0, "repurchase_intent"] == "negative"
    assert "text" not in frame.columns
    assert "user_id" not in frame.columns


def test_short_review_stays_in_rating_base_but_not_text_base() -> None:
    taxonomy = load_taxonomy(Path(__file__).resolve().parents[1] / "configs" / "taxonomy.json")
    products = pd.DataFrame(
        [{
            "parent_asin": "P1", "product_title": "Perfume", "brand": "Example",
            "price_usd": None, "product_format": "eau_de_parfum",
            "product_average_rating": 5.0, "product_rating_count": 1,
        }]
    )
    source = RUNTIME / "short_reviews.jsonl.gz"
    _write_reviews(
        source,
        [{
            "rating": 5.0, "title": "Great", "text": "Love it", "parent_asin": "P1",
            "user_id": "U1", "timestamp": 1_690_848_000_000,
            "helpful_vote": 0, "verified_purchase": False,
        }],
    )
    frame, stats = extract_tagged_reviews(source, products, taxonomy)
    assert len(frame) == 1
    assert not frame.loc[0, "text_eligible"]
    assert stats.get("text_eligible_rows", 0) == 0
