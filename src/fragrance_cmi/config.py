from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REVIEW_URL = (
    "https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/raw/"
    "review_categories/All_Beauty.jsonl.gz"
)
META_URL = (
    "https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/raw/"
    "meta_categories/meta_All_Beauty.jsonl.gz"
)


@dataclass(frozen=True)
class ProjectPaths:
    root: Path

    @property
    def raw(self) -> Path:
        return self.root / "data" / "raw"

    @property
    def processed(self) -> Path:
        return self.root / "data" / "processed"

    @property
    def figures(self) -> Path:
        return self.root / "outputs" / "figures"

    @property
    def tables(self) -> Path:
        return self.root / "outputs" / "tables"

    @property
    def reports(self) -> Path:
        return self.root / "reports"

    @property
    def taxonomy_file(self) -> Path:
        return self.root / "configs" / "taxonomy.json"

    def ensure_output_dirs(self) -> None:
        for path in (self.raw, self.processed, self.figures, self.tables, self.reports):
            path.mkdir(parents=True, exist_ok=True)


def find_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_taxonomy(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)
