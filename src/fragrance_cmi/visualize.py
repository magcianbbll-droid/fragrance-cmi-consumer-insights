from __future__ import annotations

from collections.abc import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from .config import ProjectPaths


BLUE = "#3567A8"
BLUE_LIGHT = "#AFC7E5"
GOLD = "#C89632"
ORANGE = "#D97841"
INK = "#24313D"
MUTED = "#6B7785"
GRID = "#DDE3E9"
BG = "#FBFCFD"


LABELS = {
    "longevity": "Longevity",
    "projection": "Projection",
    "scent_mismatch": "Scent mismatch",
    "authenticity": "Authenticity",
    "value": "Value / price",
    "packaging": "Packaging",
    "delivery": "Delivery",
    "irritation": "Irritation",
    "daily_or_work": "Daily / work",
    "date_or_evening": "Date / evening",
    "gifting": "Gifting",
    "travel": "Travel",
    "warm_weather": "Warm weather",
    "cold_weather": "Cold weather",
    "compliment_or_identity": "Compliment / identity",
    "citrus_fresh": "Citrus / fresh",
    "gourmand_sweet": "Gourmand / sweet",
    "amber_oriental": "Amber / oriental",
    "musk_powdery": "Musk / powdery",
    "green_herbal": "Green / herbal",
    "leather_tobacco": "Leather / tobacco",
    "performance_led": "Performance-led",
    "value_risk_reducer": "Value / risk reducer",
    "occasion_gifter": "Occasion gifter",
    "identity_seeker": "Identity seeker",
    "scent_explorer": "Scent explorer",
    "general_purchase": "General purchase",
    "eau_de_parfum": "Eau de parfum / perfume",
    "eau_de_toilette": "Eau de toilette",
    "fragrance_oil": "Fragrance oil",
    "sample_or_travel": "Sample / travel",
    "body_mist": "Body mist",
    "gift_set": "Gift set",
    "cologne": "Cologne",
    "other_fragrance": "Other fragrance",
}


def _label(value: object) -> str:
    text = str(value)
    return LABELS.get(text, text.replace("_", " ").title())


def _base_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.titlesize": 15,
            "axes.titleweight": "bold",
            "axes.labelcolor": INK,
            "axes.edgecolor": GRID,
            "axes.facecolor": BG,
            "figure.facecolor": "white",
            "xtick.color": MUTED,
            "ytick.color": INK,
            "text.color": INK,
        }
    )


def _finish(fig: plt.Figure, path, note: str | None = None) -> None:
    if note:
        fig.text(0.01, 0.01, note, fontsize=8, color=MUTED, ha="left")
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def _ranked_bar(
    frame: pd.DataFrame,
    category: str,
    value: str,
    title: str,
    subtitle: str,
    path,
    color: str = BLUE,
    percent: bool = False,
    top_n: int = 8,
) -> None:
    data = frame.nlargest(top_n, value).sort_values(value)
    fig, ax = plt.subplots(figsize=(9, 5.2))
    y = np.arange(len(data))
    values = data[value].astype(float).to_numpy()
    ax.barh(y, values, color=color, edgecolor=INK, linewidth=0.4)
    ax.set_yticks(y, [_label(v) for v in data[category]])
    ax.set_title(title, loc="left", pad=20)
    ax.text(0, 1.02, subtitle, transform=ax.transAxes, fontsize=9, color=MUTED, va="bottom")
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    max_value = values.max() if len(values) else 1
    for yi, val in zip(y, values, strict=True):
        label = f"{val:.1%}" if percent else f"{int(val):,}"
        ax.text(val + max_value * 0.015, yi, label, va="center", fontsize=9, color=INK)
    ax.set_xlim(0, max_value * 1.18 if max_value else 1)
    _finish(fig, path)


def plot_tag_summaries(paths: ProjectPaths, tables: dict[str, pd.DataFrame]) -> None:
    _ranked_bar(
        tables["pain_points"], "category", "mention_rate",
        "Pain-point mention rate",
        "Among 1–2 star, text-eligible, non-promotional reviews; multi-label",
        paths.figures / "01_pain_point_mentions.png", ORANGE, True,
    )
    _ranked_bar(
        tables["need_states"], "category", "mention_rate",
        "Use-case and emotional need mentions",
        "Among text-eligible, non-promotional reviews; multi-label",
        paths.figures / "02_need_state_mentions.png", BLUE, True,
    )
    _ranked_bar(
        tables["scent_families"], "category", "mention_rate",
        "Scent-family mention rate",
        "Among text-eligible, non-promotional reviews; multi-label",
        paths.figures / "03_scent_family_mentions.png", GOLD, True, top_n=10,
    )


def plot_weekly_tracker(paths: ProjectPaths, weekly: pd.DataFrame) -> None:
    data = weekly.copy()
    data["review_week"] = pd.to_datetime(data["review_week"])
    fig, axes = plt.subplots(2, 1, figsize=(10.5, 6.4), sharex=True, gridspec_kw={"hspace": 0.2})
    axes[0].plot(data["review_week"], data["review_volume"], color=BLUE, linewidth=2.1)
    axes[0].fill_between(data["review_week"], data["review_volume"], color=BLUE_LIGHT, alpha=0.45)
    axes[0].set_ylabel("Reviews")
    axes[0].set_title("52-week consumer voice tracker", loc="left", pad=18)
    axes[0].text(
        0, 1.02, "Weekly review volume and negative-review share",
        transform=axes[0].transAxes, fontsize=9, color=MUTED, va="bottom",
    )
    axes[1].plot(data["review_week"], data["negative_share"], color=ORANGE, linewidth=2.1)
    axes[1].set_ylabel("Negative share")
    axes[1].yaxis.set_major_formatter(lambda x, pos: f"{x:.0%}")
    axes[1].xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    for ax in axes:
        ax.grid(True, axis="y", color=GRID, linewidth=0.8)
        ax.spines[["top", "right"]].set_visible(False)
    _finish(
        fig, paths.figures / "04_weekly_voice_tracker.png",
        "Source period ends at the latest week available in Amazon Reviews 2023; this is a historical tracker template.",
    )


def plot_price_bands(paths: ProjectPaths, price: pd.DataFrame) -> None:
    data = price.copy()
    x = np.arange(len(data))
    width = 0.35
    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.bar(x - width / 2, data["positive_share"], width, label="Positive", color=BLUE, edgecolor=INK, linewidth=0.4)
    ax.bar(x + width / 2, data["negative_share"], width, label="Negative", color=ORANGE, edgecolor=INK, linewidth=0.4)
    ax.set_xticks(x, data["price_band"].astype(str))
    ax.set_ylim(0, max(1, float(data[["positive_share", "negative_share"]].max().max()) * 1.18))
    ax.yaxis.set_major_formatter(lambda v, pos: f"{v:.0%}")
    ax.set_title("Review sentiment by listed price band", loc="left", pad=20)
    ax.text(0, 1.02, "USD list price from item metadata; reviews without price are excluded", transform=ax.transAxes, fontsize=9, color=MUTED, va="bottom")
    ax.legend(frameon=False, loc="upper right")
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    _finish(fig, paths.figures / "05_price_band_sentiment.png")


def plot_brand_competition(paths: ProjectPaths, brands: pd.DataFrame) -> None:
    data = brands.nlargest(12, "review_volume").sort_values("review_volume")
    y = np.arange(len(data))
    fig, axes = plt.subplots(1, 2, figsize=(12, 6), gridspec_kw={"width_ratios": [1.35, 1], "wspace": 0.12})
    axes[0].barh(y, data["review_volume"], color=BLUE, edgecolor=INK, linewidth=0.35)
    axes[0].set_yticks(y, [_label(v) for v in data["brand"]])
    axes[0].set_title("Competitive review footprint", loc="left", pad=20)
    axes[0].text(0, 1.02, "Brands with at least 20 reviews; top 12 by volume", transform=axes[0].transAxes, fontsize=9, color=MUTED, va="bottom")
    axes[0].xaxis.grid(True, color=GRID)
    axes[0].set_axisbelow(True)
    axes[1].scatter(data["positive_share"], y, color=GOLD, edgecolor=INK, s=65, linewidth=0.5)
    axes[1].set_yticks(y, [])
    axes[1].set_xlim(0, 1)
    axes[1].xaxis.set_major_formatter(lambda v, pos: f"{v:.0%}")
    axes[1].set_xlabel("Positive-review share")
    axes[1].axvline(float(brands["positive_share"].median()), color=MUTED, linestyle="--", linewidth=1)
    axes[1].xaxis.grid(True, color=GRID)
    for ax in axes:
        ax.spines[["top", "right", "left"]].set_visible(False)
    _finish(fig, paths.figures / "06_brand_competition.png")


def plot_segments_and_formats(paths: ProjectPaths, tables: dict[str, pd.DataFrame]) -> None:
    _ranked_bar(
        tables["behavior_segments"], "behavior_segment", "share_of_reviews",
        "Behavioral need-state segments",
        "Deterministic, review-level segment; no demographic inference",
        paths.figures / "07_behavior_segments.png", BLUE, True, top_n=8,
    )
    _ranked_bar(
        tables["product_formats"], "product_format", "share_of_reviews",
        "Review mix by fragrance format",
        "Share of deduplicated fragrance reviews",
        paths.figures / "08_product_format_mix.png", GOLD, True, top_n=9,
    )

    repurchase = tables["repurchase_intent"].copy()
    repurchase = repurchase.loc[repurchase["repurchase_intent"].isin(["positive", "negative"])]
    if len(repurchase):
        total = repurchase["review_volume"].sum()
        repurchase["explicit_share"] = repurchase["review_volume"] / total
        _ranked_bar(
            repurchase, "repurchase_intent", "explicit_share",
            "Explicit repurchase intent",
            "Share among reviews with an explicit buy-again / not-buy-again signal",
            paths.figures / "09_explicit_repurchase_intent.png", BLUE, True, top_n=2,
        )


def build_all_figures(paths: ProjectPaths, tables: dict[str, pd.DataFrame]) -> None:
    _base_style()
    paths.figures.mkdir(parents=True, exist_ok=True)
    plot_tag_summaries(paths, tables)
    plot_weekly_tracker(paths, tables["weekly_tracker"])
    plot_price_bands(paths, tables["price_bands"])
    plot_brand_competition(paths, tables["brand_scorecard"])
    plot_segments_and_formats(paths, tables)
