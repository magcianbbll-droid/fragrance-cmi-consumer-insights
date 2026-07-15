# Data policy

The analysis uses the public **Amazon Reviews 2023 / All Beauty** review and
metadata files published by McAuley Lab. Raw third-party files are downloaded
locally by `scripts/download_data.py` and are excluded from Git.

Local files under `data/processed/` contain derived classifications only and are
excluded from Git because they still carry third-party product metadata. Review
text and raw user identifiers are never persisted. The pipeline creates an
irreversible short review key solely for deduplication. Aggregate tables safe
for portfolio review are committed under `outputs/tables/`.

See [`DATA_SOURCES.md`](../DATA_SOURCES.md) and
[`docs/methodology.md`](../docs/methodology.md) for source and scope details.
