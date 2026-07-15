# Methodology

## Business question

Which fragrance consumer needs, pain points and competitive patterns should a
brand test first, and how can the insight be converted into a 90-day validation
plan?

## Pipeline

1. Download the All Beauty review and metadata files from the official
   McAuley Lab endpoints.
2. Identify wearable-fragrance products using an include/exclude taxonomy.
   Exclude home fragrance, candles, diffusers, cleaners and unrelated wash-off
   beauty; retain perfume, cologne, body mist, fragrance oil, gift and trial
   formats.
3. Join reviews to item metadata on `parent_asin`.
4. Deduplicate on a SHA-256 key built from reviewer id, parent ASIN, timestamp
   and normalized text. Raw reviewer ids are never written to processed files.
5. Require a valid timestamp and 1–5 rating. Keep short reviews for rating
   summaries but exclude them from text-tag denominators.
6. Apply transparent, multi-label English lexicons for pain points, need states
   and scent families. Tag explicit repurchase language separately.
7. Build mutually exclusive behavioral segments through documented priority
   rules. Do not infer demographics.
8. Aggregate to weekly, brand, price-band, format and tag-level tables; render
   the decision-oriented report and tracker workbook.

## Promotion and price handling

Price discussion is retained because it is part of consumer value perception.
Only short text containing affiliate/coupon/promo markers is flagged as pure
promotional noise and removed from text-tag denominators. It remains auditable
in the processed row-level file.

## Limitations

The lexicon favors precision and auditability over full recall. Sarcasm,
negation and emerging slang can be missed. A production deployment should add
a stratified human-label QA sample and calculate per-label precision/recall or
inter-annotator agreement before automating decisions.
