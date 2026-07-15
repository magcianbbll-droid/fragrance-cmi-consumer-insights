# Label codebook and iteration log

The taxonomy is stored in `configs/taxonomy.json`. Pain, need-state and scent
labels are multi-label. A review can mention more than one pain or need. The
behavioral segment is a single deterministic label for activation planning.

## Label dimensions

### Pain points

- `longevity`: fades quickly, does not last, weak longevity
- `projection`: barely detectable, no projection, skin scent
- `scent_mismatch`: different from expectation, excessive sweetness/strength,
  headache or nausea
- `authenticity`: fake, counterfeit, diluted, not authentic
- `value`: overpriced, not worth it, poor value
- `packaging`: leakage, broken bottle/cap, sprayer or atomizer failure
- `delivery`: late, missing or damaged in transit
- `irritation`: rash, allergy, burning or itching

Pain-point rates use negative 1–2 star, text-eligible, non-promotional reviews
as the denominator.

### Need states

- gifting
- compliment / identity expression
- daily / work
- travel / portability
- date / evening
- warm-weather and cold-weather use

The taxonomy only labels explicit language. It does not infer a scenario from
the product type or rating.

### Scent families

Consumer vocabulary is grouped into floral, fruity, citrus/fresh,
gourmand/sweet, woody, amber/oriental, musk/powdery, aquatic, green/herbal,
spicy and leather/tobacco. These are consumer-language families, not official
brand fragrance classifications.

## Iteration log

1. **Product filter v1:** included product feature text. QA found makeup and
   skincare using “fragrance-free” language.
2. **Product filter v2:** restricted evidence to title/category and added
   explicit fragrance-free, home-fragrance and empty-bottle exclusions.
3. **Need-state v2:** QA found the word `work` in “doesn't work” inflated the
   work/office scenario. It was replaced with contextual phrases such as
   `at work`, `for work`, `wear to work`, `office` and `workplace`.

These changes are covered by unit tests. A production rollout should add a
stratified human-label audit and calculate per-label precision/recall and
inter-annotator agreement before automating high-impact decisions.
