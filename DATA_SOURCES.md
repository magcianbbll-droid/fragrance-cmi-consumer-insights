# Data sources

## Amazon Reviews 2023 — All Beauty

- Publisher: McAuley Lab, University of California San Diego
- Project page: <https://amazon-reviews-2023.github.io/>
- Review file: <https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/raw/review_categories/All_Beauty.jsonl.gz>
- Metadata file: <https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/raw/meta_categories/meta_All_Beauty.jsonl.gz>
- Source coverage: reviews through September 2023
- Fields used: rating, title, review text, timestamp, helpful votes, verified
  purchase, parent ASIN; product title, store/brand, category, price, aggregate
  rating and rating count.
- Review file SHA-256 (downloaded 2026-07-15):
  `ee00e66835567c3f12fde6a482f8d7055c22cac2d0924f677263affdd8a0e349`
- Metadata file SHA-256 (downloaded 2026-07-15):
  `51f8255c2794afd60e274c10d3e2d09dc1f671eba4ba35f74f748d8631216d05`

The source dataset contains about 701,500 All Beauty reviews and 112,600
reviewed items. This project filters the category to wearable fragrance using a
documented keyword and exclusion taxonomy.

## Reproducibility

`scripts/download_data.py` records the source URLs, byte sizes and SHA-256
hashes in a local ignored manifest. Raw data is not committed. The public report
is generated from derived tables produced by `scripts/run_pipeline.py`.
