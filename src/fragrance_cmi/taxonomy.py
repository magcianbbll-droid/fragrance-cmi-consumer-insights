from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any


SPACE_RE = re.compile(r"\s+")


def normalize_text(value: Any) -> str:
    text = "" if value is None else str(value)
    return SPACE_RE.sub(" ", text.casefold()).strip()


def contains_phrase(text: str, phrase: str) -> bool:
    phrase = normalize_text(phrase)
    if not phrase:
        return False
    pattern = r"(?<!\w)" + re.escape(phrase).replace(r"\ ", r"\s+") + r"(?!\w)"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def has_any(text: str, phrases: Iterable[str]) -> bool:
    return any(contains_phrase(text, phrase) for phrase in phrases)


def is_fragrance_product(product: dict[str, Any], taxonomy: dict[str, Any]) -> bool:
    title = normalize_text(product.get("title"))
    fragrance_free_pattern = re.compile(
        r"(?:fragrance|perfume)[\s-]*free|free\s+(?:from|of).{0,120}(?:fragrance|perfume)|without.{0,120}(?:fragrance|perfume)",
        flags=re.IGNORECASE,
    )
    if fragrance_free_pattern.search(title):
        return False
    searchable = " ".join(
        [
            title,
            " ".join(map(str, product.get("categories") or [])),
        ]
    )
    normalized = normalize_text(searchable)
    return has_any(normalized, taxonomy["product_include"]) and not has_any(
        normalized, taxonomy["product_exclude"]
    )


def classify_format(text: str, formats: dict[str, list[str]]) -> str:
    normalized = normalize_text(text)
    for label, phrases in formats.items():
        if has_any(normalized, phrases):
            return label
    return "other_fragrance"


def classify_multilabel(text: str, definitions: dict[str, list[str]]) -> list[str]:
    normalized = normalize_text(text)
    return [label for label, phrases in definitions.items() if has_any(normalized, phrases)]


def classify_repurchase(text: str, taxonomy: dict[str, Any]) -> str:
    normalized = normalize_text(text)
    if has_any(normalized, taxonomy["repurchase_negative"]):
        return "negative"
    if has_any(normalized, taxonomy["repurchase_positive"]):
        return "positive"
    return "not_explicit"


def clean_brand(product: dict[str, Any]) -> str:
    details = product.get("details") or {}
    brand = details.get("Brand") or product.get("store") or details.get("Manufacturer")
    brand = SPACE_RE.sub(" ", str(brand or "Unknown")).strip()
    if not brand or brand.casefold() in {"none", "nan", "unknown"}:
        return "Unknown"
    return brand[:80]
