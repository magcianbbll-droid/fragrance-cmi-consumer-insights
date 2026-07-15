from __future__ import annotations

import hashlib
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from .config import ProjectPaths, load_taxonomy
from .io import iter_jsonl_gz, sha256_file, write_json
from .taxonomy import (
    classify_format,
    classify_multilabel,
    classify_repurchase,
    clean_brand,
    is_fragrance_product,
    normalize_text,
)


def _float_or_none(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _int_or_zero(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _sentiment(rating: float) -> str:
    if rating >= 4:
        return "positive"
    if rating <= 2:
        return "negative"
    return "neutral"


def _review_key(review: dict[str, Any], normalized_text: str) -> str:
    raw = "|".join(
        [
            str(review.get("user_id") or ""),
            str(review.get("parent_asin") or ""),
            str(review.get("timestamp") or ""),
            normalized_text,
        ]
    )
    return hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest()[:20]


def _behavior_segment(
    pain_points: list[str],
    need_states: list[str],
    scent_families: list[str],
    repurchase: str,
    product_format: str,
    price_discussion: bool,
) -> str:
    if any(tag in {"longevity", "projection"} for tag in pain_points):
        return "performance_led"
    if (
        price_discussion
        or any(tag in {"value", "authenticity"} for tag in pain_points)
        or product_format in {"sample_or_travel", "gift_set"}
    ):
        return "value_risk_reducer"
    if "gifting" in need_states:
        return "occasion_gifter"
    if "compliment_or_identity" in need_states or repurchase == "positive":
        return "identity_seeker"
    if scent_families:
        return "scent_explorer"
    return "general_purchase"


def extract_fragrance_products(
    metadata_file: Path, taxonomy: dict[str, Any]
) -> tuple[pd.DataFrame, dict[str, int]]:
    products: dict[str, dict[str, Any]] = {}
    source_rows = 0
    duplicate_parent_rows = 0
    for product in iter_jsonl_gz(metadata_file):
        source_rows += 1
        if not is_fragrance_product(product, taxonomy):
            continue
        parent_asin = str(product.get("parent_asin") or "").strip()
        if not parent_asin:
            continue
        if parent_asin in products:
            duplicate_parent_rows += 1
        title = str(product.get("title") or "").strip()
        products[parent_asin] = {
            "parent_asin": parent_asin,
            "product_title": title,
            "brand": clean_brand(product),
            "price_usd": _float_or_none(product.get("price")),
            "product_format": classify_format(title, taxonomy["formats"]),
            "product_average_rating": _float_or_none(product.get("average_rating")),
            "product_rating_count": _int_or_zero(product.get("rating_number")),
        }
    frame = pd.DataFrame(products.values()).sort_values("parent_asin").reset_index(drop=True)
    stats = {
        "source_metadata_rows": source_rows,
        "fragrance_product_rows": len(frame),
        "duplicate_parent_metadata_rows": duplicate_parent_rows,
    }
    return frame, stats


def extract_tagged_reviews(
    review_file: Path,
    products: pd.DataFrame,
    taxonomy: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    product_lookup = products.set_index("parent_asin").to_dict(orient="index")
    seen_keys: set[str] = set()
    rows: list[dict[str, Any]] = []
    counters: Counter[str] = Counter()

    price_terms = [
        "price", "expensive", "cheap", "value", "worth", "sale", "discount",
        "coupon", "deal", "cost", "affordable", "overpriced",
    ]
    promo_terms = ["coupon", "discount code", "affiliate", "sponsored", "promo code", "link in bio"]

    for review in iter_jsonl_gz(review_file):
        counters["source_review_rows"] += 1
        parent_asin = str(review.get("parent_asin") or "").strip()
        product = product_lookup.get(parent_asin)
        if product is None:
            continue
        counters["matched_review_rows"] += 1

        title = str(review.get("title") or "")
        body = str(review.get("text") or "")
        normalized = normalize_text(f"{title} {body}")
        key = _review_key(review, normalized)
        if key in seen_keys:
            counters["duplicate_review_rows"] += 1
            continue
        seen_keys.add(key)

        timestamp = pd.to_datetime(review.get("timestamp"), unit="ms", utc=True, errors="coerce")
        if pd.isna(timestamp):
            counters["invalid_timestamp_rows"] += 1
            continue

        rating = _float_or_none(review.get("rating"))
        if rating is None or rating < 1 or rating > 5:
            counters["invalid_rating_rows"] += 1
            continue

        word_count = len(normalized.split())
        text_eligible = len(normalized) >= 20 and word_count >= 4
        if text_eligible:
            counters["text_eligible_rows"] += 1
            pain_points = classify_multilabel(normalized, taxonomy["pain_points"])
            need_states = classify_multilabel(normalized, taxonomy["need_states"])
            scent_families = classify_multilabel(normalized, taxonomy["scent_families"])
            repurchase = classify_repurchase(normalized, taxonomy)
            price_discussion = any(term in normalized for term in price_terms)
            pure_promo_noise = any(term in normalized for term in promo_terms) and word_count < 25
        else:
            pain_points, need_states, scent_families = [], [], []
            repurchase = "not_explicit"
            price_discussion = False
            pure_promo_noise = False

        segment = _behavior_segment(
            pain_points,
            need_states,
            scent_families,
            repurchase,
            str(product["product_format"]),
            price_discussion,
        )
        record: dict[str, Any] = {
            "review_key": key,
            "parent_asin": parent_asin,
            "review_date": timestamp.date().isoformat(),
            "review_week": (timestamp - pd.Timedelta(days=timestamp.weekday())).date().isoformat(),
            "rating": rating,
            "sentiment": _sentiment(rating),
            "verified_purchase": bool(review.get("verified_purchase")),
            "helpful_votes": _int_or_zero(review.get("helpful_vote", review.get("helpful_votes"))),
            "text_length": len(normalized),
            "word_count": word_count,
            "text_eligible": text_eligible,
            "price_discussion": price_discussion,
            "pure_promo_noise": pure_promo_noise,
            "repurchase_intent": repurchase,
            "behavior_segment": segment,
            **product,
        }
        for prefix, definitions, selected in (
            ("pain", taxonomy["pain_points"], pain_points),
            ("need", taxonomy["need_states"], need_states),
            ("scent", taxonomy["scent_families"], scent_families),
        ):
            selected_set = set(selected)
            for label in definitions:
                record[f"{prefix}_{label}"] = label in selected_set
        rows.append(record)

    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame = frame.sort_values(["review_date", "review_key"]).reset_index(drop=True)
    stats: dict[str, Any] = dict(counters)
    stats["deduplicated_review_rows"] = len(frame)
    stats["distinct_review_products"] = int(frame["parent_asin"].nunique()) if len(frame) else 0
    stats["distinct_brands"] = int(frame["brand"].nunique()) if len(frame) else 0
    stats["review_date_min"] = str(frame["review_date"].min()) if len(frame) else None
    stats["review_date_max"] = str(frame["review_date"].max()) if len(frame) else None
    stats["text_eligible_rate"] = round(
        stats.get("text_eligible_rows", 0) / len(frame), 6
    ) if len(frame) else 0
    stats["verified_purchase_rate"] = round(float(frame["verified_purchase"].mean()), 6) if len(frame) else 0
    stats["review_price_coverage_rate"] = round(float(frame["price_usd"].notna().mean()), 6) if len(frame) else 0
    stats["pure_promo_noise_rate"] = round(float(frame["pure_promo_noise"].mean()), 6) if len(frame) else 0
    return frame, stats


def run_cleaning(paths: ProjectPaths) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    paths.ensure_output_dirs()
    taxonomy = load_taxonomy(paths.taxonomy_file)
    metadata_file = paths.raw / "meta_All_Beauty.jsonl.gz"
    review_file = paths.raw / "All_Beauty.jsonl.gz"
    for source in (metadata_file, review_file):
        if not source.exists():
            raise FileNotFoundError(f"Missing {source}. Run scripts/download_data.py first.")

    products, product_stats = extract_fragrance_products(metadata_file, taxonomy)
    reviews, review_stats = extract_tagged_reviews(review_file, products, taxonomy)

    products.to_csv(paths.processed / "fragrance_products.csv", index=False, encoding="utf-8-sig")
    reviews.to_csv(paths.processed / "reviews_tagged_no_text.csv", index=False, encoding="utf-8-sig")

    quality = {
        "source": "McAuley Lab Amazon Reviews 2023 / All_Beauty",
        "grain": "one deduplicated review per review_key",
        **product_stats,
        **review_stats,
        "product_price_coverage_rate": round(float(products["price_usd"].notna().mean()), 6),
        "taxonomy_sha256": sha256_file(paths.taxonomy_file),
        "privacy": "Review text and raw user identifiers are not persisted in processed outputs.",
    }
    write_json(quality, paths.tables / "data_quality_summary.json")
    return products, reviews, quality
