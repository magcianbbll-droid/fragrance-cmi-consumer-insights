from pathlib import Path

from fragrance_cmi.config import load_taxonomy
from fragrance_cmi.taxonomy import (
    classify_format,
    classify_multilabel,
    classify_repurchase,
    is_fragrance_product,
)


TAXONOMY = load_taxonomy(Path(__file__).resolve().parents[1] / "configs" / "taxonomy.json")


def test_wearable_fragrance_is_included() -> None:
    product = {
        "title": "Example Eau de Parfum Spray for Women 50 ml",
        "categories": ["Beauty", "Fragrance"],
    }
    assert is_fragrance_product(product, TAXONOMY)


def test_fragrance_free_makeup_is_excluded() -> None:
    product = {
        "title": "Eyeshadow Palette Free from Oil, Fragrance, Parabens and Alcohol",
        "categories": ["Beauty", "Makeup"],
    }
    assert not is_fragrance_product(product, TAXONOMY)


def test_home_fragrance_and_empty_bottles_are_excluded() -> None:
    diffuser = {"title": "Luxury Home Fragrance Reed Diffuser", "categories": []}
    bottle = {"title": "Refillable Empty Perfume Atomizer Bottle", "categories": []}
    assert not is_fragrance_product(diffuser, TAXONOMY)
    assert not is_fragrance_product(bottle, TAXONOMY)


def test_multilabel_and_repurchase_are_transparent() -> None:
    text = "I wear this at work. Sweet vanilla, but it doesn't last. I will not buy again."
    pains = classify_multilabel(text, TAXONOMY["pain_points"])
    needs = classify_multilabel(text, TAXONOMY["need_states"])
    scents = classify_multilabel(text, TAXONOMY["scent_families"])
    assert "longevity" in pains
    assert "daily_or_work" in needs
    assert "gourmand_sweet" in scents
    assert classify_repurchase(text, TAXONOMY) == "negative"


def test_plain_doesnt_work_is_not_an_office_scenario() -> None:
    text = "The sprayer doesn't work and the bottle leaked."
    needs = classify_multilabel(text, TAXONOMY["need_states"])
    assert "daily_or_work" not in needs


def test_format_priority_preserves_trial_format() -> None:
    title = "Mini perfume discovery set travel size"
    assert classify_format(title, TAXONOMY["formats"]) == "sample_or_travel"
