# Metric definitions

| Metric | Definition | Denominator / grain |
|---|---|---|
| Analysis review | A fragrance-linked review with valid 1–5 rating and timestamp, after composite-key deduplication | One `review_key` |
| Text-eligible review | Normalized title + body has at least 20 characters and 4 tokens | Analysis reviews |
| Positive review share | Rating is 4 or 5 | Analysis reviews in the cut |
| Negative review share | Rating is 1 or 2 | Analysis reviews in the cut |
| Pain-point mention rate | Review matches a transparent pain lexicon | Negative, text-eligible, non-promotional reviews |
| Need-state mention rate | Review matches a transparent use-case/emotional lexicon | Text-eligible, non-promotional reviews |
| Scent-family mention rate | Review contains at least one consumer scent term | Text-eligible, non-promotional reviews |
| Explicit repurchase share | Positive/negative buy-again phrase | Reviews with an explicit repurchase signal only |
| Verified purchase share | Source flag equals true | Analysis reviews in the cut |
| Brand review footprint | Count of reviews linked to a normalized store/brand | Brand; minimum 20 reviews for scorecard |
| Price-band sentiment | Positive/negative review share by metadata list price | Reviews with non-null USD price |

Pain, need and scent fields are multi-label. Their mention rates are not expected
to sum to 100%. Behavioral segments are mutually exclusive rule-based labels at
review grain and are not demographic segments.
