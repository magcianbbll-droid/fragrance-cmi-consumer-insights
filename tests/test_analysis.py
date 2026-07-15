import pandas as pd

from fragrance_cmi.analysis import _tag_summary


def test_tag_summary_uses_explicit_denominator_and_multilabel_mentions() -> None:
    reviews = pd.DataFrame(
        {
            "pain_value": [True, False, True],
            "pain_longevity": [True, True, False],
        }
    )
    mask = pd.Series([True, True, False])
    result = _tag_summary(reviews, "pain_", mask, "negative eligible reviews")
    result = result.set_index("category")
    assert result.loc["value", "denominator"] == 2
    assert result.loc["value", "mention_rate"] == 0.5
    assert result.loc["longevity", "mention_rate"] == 1.0
    assert result["share_of_tag_mentions"].sum() == 1.0
