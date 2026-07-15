from __future__ import annotations

import gzip
import hashlib
import json
import re
import shutil
import time
import urllib.request
from collections.abc import Iterator
from pathlib import Path
from typing import Any


def download_file(url: str, destination: Path, chunk_size: int = 1024 * 1024) -> Path:
    """Download a file atomically and resume an interrupted partial download."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size > 0:
        return destination

    temporary = destination.with_suffix(destination.suffix + ".part")
    existing_bytes = temporary.stat().st_size if temporary.exists() else 0
    headers = {"User-Agent": "fragrance-cmi/1.0"}
    if existing_bytes:
        headers["Range"] = f"bytes={existing_bytes}-"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=120) as response:
        resumed = existing_bytes > 0 and getattr(response, "status", None) == 206
        mode = "ab" if resumed else "wb"
        with temporary.open(mode) as out:
            if resumed:
                content_range = response.headers.get("Content-Range", "")
                match = re.match(r"bytes\s+(\d+)-", content_range)
                range_start = int(match.group(1)) if match else existing_bytes
                if range_start > existing_bytes:
                    raise OSError(
                        f"Server resumed at {range_start}, after local byte {existing_bytes}"
                    )
                overlap = existing_bytes - range_start
                while overlap:
                    discarded = response.read(min(chunk_size, overlap))
                    if not discarded:
                        raise OSError("Server response ended while skipping range overlap")
                    overlap -= len(discarded)
            while chunk := response.read(chunk_size):
                out.write(chunk)
    for attempt in range(5):
        try:
            temporary.replace(destination)
            break
        except PermissionError:
            if attempt == 4:
                raise
            time.sleep(0.25 * (attempt + 1))
    return destination


def iter_jsonl_gz(path: Path) -> Iterator[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in {path} at line {line_number}") from exc


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(data: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2, default=str)


def remove_tree_contents(path: Path) -> None:
    if not path.exists():
        return
    for child in path.iterdir():
        if child.name == ".gitkeep":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
