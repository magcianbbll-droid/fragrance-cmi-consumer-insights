# Validation report

## Overall assessment: Ready to share with caveats

The project is reproducible and the headline calculations reconcile to saved
aggregate outputs. It is ready as a portfolio CMI case study, provided the
historical Amazon scope and lexicon limitations remain visible.

## Calculation spot-checks

- Review reconciliation: 14,813 fragrance-matched reviews minus 166 duplicate
  keys equals 14,647 analysis reviews.
- Text base: 13,859 reviews are text-eligible, 94.6% of the analysis base.
- Pain denominator: 2,507 text-eligible negative reviews out of 2,561 total
  1–2 star reviews.
- Price coverage: 4,155 + 2,476 + 1,226 + 197 = 8,054 priced reviews;
  8,054 / 14,647 = 55.0%.
- Explicit repurchase base: 316 positive + 38 negative = 354; positive explicit
  intent is 89.3% of explicit signals, not the full review base and not an
  observed repeat-purchase rate.
- Pain concentration: value (192), scent mismatch (176) and authenticity (132)
  contribute 500 of 713 detected pain-tag mentions, or 70.1%. Because pain is
  multi-label, this is a share of tag mentions, not a unique-consumer share.

## Data-quality findings

- Both gzip sources were fully parsed: 701,528 review rows and 112,590 metadata
  rows. Local download hashes are recorded by the downloader.
- Product QA removed fragrance-free makeup/skincare, home fragrance and empty
  perfume containers from the wearable-fragrance set.
- Need-state QA removed the ambiguous word `work`, which incorrectly matched
  “doesn't work”; contextual work/office phrases remain.
- Processed row-level outputs contain no full review text or raw user id.

## Visualization and workbook review

- Nine static figures were rendered and inspected with explicit denominators.
- The 13-sheet Excel tracker was rendered sheet by sheet.
- Dashboard formulas reconcile to the analysis sheet; formula-error scan found
  no `#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?` or `#N/A` results.
- Date labels and source number formats were corrected after visual QA.

## Required caveats

- Source coverage ends 2023-08-30 and does not represent a live 2026 market.
- Amazon review authors are a selected population; results are not population
  prevalence estimates and cannot be generalized to China social platforms.
- Metadata store/brand and list price have missingness and normalization risk;
  review footprint is not sales or market share.
- Lexicon tagging is transparent but incomplete. Production use requires a
  stratified human-label audit and ongoing drift monitoring.
