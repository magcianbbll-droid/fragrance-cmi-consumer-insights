from __future__ import annotations

from pathlib import Path
from typing import Any
import json

import numpy as np
import pandas as pd

from .config import ProjectPaths
from .io import write_json


PRICE_BINS = [-np.inf, 25, 50, 100, np.inf]
PRICE_LABELS = ["Under $25", "$25–49", "$50–99", "$100+"]


def _share(series: pd.Series, value: Any = True) -> float:
    return float((series == value).mean()) if len(series) else 0.0


def _tag_summary(
    reviews: pd.DataFrame,
    prefix: str,
    denominator_mask: pd.Series,
    label: str,
) -> pd.DataFrame:
    denominator = int(denominator_mask.sum())
    rows = []
    for column in sorted(c for c in reviews.columns if c.startswith(prefix)):
        mentions = int((reviews.loc[denominator_mask, column] == True).sum())  # noqa: E712
        rows.append(
            {
                "category": column.removeprefix(prefix),
                "mentions": mentions,
                "denominator": denominator,
                "mention_rate": mentions / denominator if denominator else 0,
                "denominator_definition": label,
            }
        )
    frame = pd.DataFrame(rows).sort_values(["mentions", "category"], ascending=[False, True])
    if len(frame):
        total_mentions = int(frame["mentions"].sum())
        frame["share_of_tag_mentions"] = frame["mentions"] / total_mentions if total_mentions else 0
        frame["cumulative_tag_share"] = frame["share_of_tag_mentions"].cumsum()
    return frame.reset_index(drop=True)


def _weekly_tracker(reviews: pd.DataFrame) -> pd.DataFrame:
    frame = reviews.copy()
    frame["review_week"] = pd.to_datetime(frame["review_week"])
    max_week = frame["review_week"].max()
    start_week = max_week - pd.Timedelta(weeks=51)
    frame = frame.loc[frame["review_week"].between(start_week, max_week)]
    grouped = frame.groupby("review_week", as_index=True).agg(
        review_volume=("review_key", "count"),
        average_rating=("rating", "mean"),
        positive_reviews=("sentiment", lambda s: int((s == "positive").sum())),
        negative_reviews=("sentiment", lambda s: int((s == "negative").sum())),
        verified_reviews=("verified_purchase", "sum"),
        helpful_votes=("helpful_votes", "sum"),
        price_discussions=("price_discussion", "sum"),
        text_eligible_reviews=("text_eligible", "sum"),
    )
    full_index = pd.date_range(start=start_week, end=max_week, freq="7D", name="review_week")
    grouped = grouped.reindex(full_index)
    count_columns = [
        "review_volume", "positive_reviews", "negative_reviews", "verified_reviews",
        "helpful_votes", "price_discussions", "text_eligible_reviews",
    ]
    grouped[count_columns] = grouped[count_columns].fillna(0).astype(int)
    grouped["average_rating"] = grouped["average_rating"].astype(float)
    grouped["positive_share"] = grouped["positive_reviews"].div(grouped["review_volume"].replace(0, np.nan))
    grouped["negative_share"] = grouped["negative_reviews"].div(grouped["review_volume"].replace(0, np.nan))
    grouped["verified_share"] = grouped["verified_reviews"].div(grouped["review_volume"].replace(0, np.nan))
    grouped["price_discussion_share"] = grouped["price_discussions"].div(
        grouped["text_eligible_reviews"].replace(0, np.nan)
    )
    return grouped.reset_index()


def _brand_scorecard(reviews: pd.DataFrame) -> pd.DataFrame:
    known = reviews.loc[reviews["brand"].ne("Unknown")].copy()
    grouped = known.groupby("brand", as_index=False).agg(
        review_volume=("review_key", "count"),
        product_count=("parent_asin", "nunique"),
        average_rating=("rating", "mean"),
        median_price_usd=("price_usd", "median"),
        price_coverage=("price_usd", lambda s: float(s.notna().mean())),
        verified_share=("verified_purchase", "mean"),
        helpful_votes=("helpful_votes", "sum"),
        positive_share=("sentiment", lambda s: float((s == "positive").mean())),
        negative_share=("sentiment", lambda s: float((s == "negative").mean())),
        longevity_mentions=("pain_longevity", "sum"),
        value_mentions=("pain_value", "sum"),
        authenticity_mentions=("pain_authenticity", "sum"),
    )
    grouped = grouped.loc[grouped["review_volume"] >= 20]
    grouped["brand_opportunity_score"] = (
        grouped["negative_share"] * np.log1p(grouped["review_volume"])
    )
    return grouped.sort_values(["review_volume", "brand"], ascending=[False, True]).reset_index(drop=True)


def _price_band_summary(reviews: pd.DataFrame) -> pd.DataFrame:
    priced = reviews.loc[reviews["price_usd"].notna()].copy()
    priced["price_band"] = pd.cut(
        priced["price_usd"], bins=PRICE_BINS, labels=PRICE_LABELS, right=False
    )
    grouped = priced.groupby("price_band", observed=False, as_index=False).agg(
        review_volume=("review_key", "count"),
        product_count=("parent_asin", "nunique"),
        average_rating=("rating", "mean"),
        positive_share=("sentiment", lambda s: float((s == "positive").mean())),
        negative_share=("sentiment", lambda s: float((s == "negative").mean())),
        price_discussion_share=("price_discussion", "mean"),
        repurchase_positive=("repurchase_intent", lambda s: int((s == "positive").sum())),
    )
    return grouped


def _simple_distribution(reviews: pd.DataFrame, column: str) -> pd.DataFrame:
    grouped = reviews.groupby(column, dropna=False, as_index=False).agg(
        review_volume=("review_key", "count"),
        average_rating=("rating", "mean"),
        positive_share=("sentiment", lambda s: float((s == "positive").mean())),
        negative_share=("sentiment", lambda s: float((s == "negative").mean())),
    )
    grouped["share_of_reviews"] = grouped["review_volume"] / len(reviews)
    return grouped.sort_values(["review_volume", column], ascending=[False, True]).reset_index(drop=True)


def run_analysis(
    paths: ProjectPaths,
    products: pd.DataFrame,
    reviews: pd.DataFrame,
    quality: dict[str, Any],
) -> dict[str, pd.DataFrame]:
    if reviews.empty:
        raise ValueError("No fragrance reviews were available for analysis.")

    eligible = reviews["text_eligible"] & ~reviews["pure_promo_noise"]
    negative_eligible = eligible & reviews["sentiment"].eq("negative")

    tables = {
        "pain_points": _tag_summary(
            reviews, "pain_", negative_eligible,
            "negative (1–2 star), text-eligible, non-promotional reviews",
        ),
        "need_states": _tag_summary(
            reviews, "need_", eligible,
            "text-eligible, non-promotional fragrance reviews",
        ),
        "scent_families": _tag_summary(
            reviews, "scent_", eligible,
            "text-eligible, non-promotional fragrance reviews",
        ),
        "weekly_tracker": _weekly_tracker(reviews),
        "brand_scorecard": _brand_scorecard(reviews),
        "price_bands": _price_band_summary(reviews),
        "behavior_segments": _simple_distribution(reviews.loc[eligible], "behavior_segment"),
        "product_formats": _simple_distribution(reviews, "product_format"),
        "repurchase_intent": _simple_distribution(reviews.loc[eligible], "repurchase_intent"),
    }
    for name, table in tables.items():
        table.to_csv(paths.tables / f"{name}.csv", index=False, encoding="utf-8-sig")

    workbook_payload = {
        name: json.loads(table.to_json(orient="records", date_format="iso"))
        for name, table in tables.items()
    }
    write_json(workbook_payload, paths.tables / "workbook_payload.json")

    pain = tables["pain_points"]
    needs = tables["need_states"]
    scents = tables["scent_families"]
    brands = tables["brand_scorecard"]
    repurchase = tables["repurchase_intent"]
    explicit_repurchase = repurchase.loc[repurchase["repurchase_intent"].ne("not_explicit")]

    summary = {
        "data_as_of": quality["review_date_max"],
        "source_review_rows": quality["source_review_rows"],
        "fragrance_product_rows": quality["fragrance_product_rows"],
        "analysis_review_rows": len(reviews),
        "analysis_product_rows": int(reviews["parent_asin"].nunique()),
        "analysis_brand_rows": int(reviews["brand"].nunique()),
        "text_eligible_rows": int(eligible.sum()),
        "negative_review_rows": int(reviews["sentiment"].eq("negative").sum()),
        "negative_text_eligible_rows": int(negative_eligible.sum()),
        "verified_purchase_share": float(reviews["verified_purchase"].mean()),
        "price_coverage_share": float(reviews["price_usd"].notna().mean()),
        "average_rating": float(reviews["rating"].mean()),
        "positive_review_share": _share(reviews["sentiment"], "positive"),
        "negative_review_share": _share(reviews["sentiment"], "negative"),
        "explicit_repurchase_rows": int(explicit_repurchase["review_volume"].sum()) if len(explicit_repurchase) else 0,
        "top_pain_point": pain.iloc[0]["category"] if len(pain) else None,
        "top_pain_mention_rate": float(pain.iloc[0]["mention_rate"]) if len(pain) else 0,
        "top_need_state": needs.iloc[0]["category"] if len(needs) else None,
        "top_need_mention_rate": float(needs.iloc[0]["mention_rate"]) if len(needs) else 0,
        "top_scent_family": scents.iloc[0]["category"] if len(scents) else None,
        "top_scent_mention_rate": float(scents.iloc[0]["mention_rate"]) if len(scents) else 0,
        "leading_brand_by_review_volume": brands.iloc[0]["brand"] if len(brands) else None,
        "leading_brand_review_volume": int(brands.iloc[0]["review_volume"]) if len(brands) else 0,
        "multi_label_note": "Need, pain and scent tags are multi-label; mention rates do not sum to 100%.",
    }
    write_json(summary, paths.tables / "summary_metrics.json")
    return tables
