"""
loader.py — Load raw facility JSON files from /research into Postgres.

Usage:
    python -m data_pipeline.scripts.loader --file research/facilities_state_2024-01-01.json
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def load_facilities(file_path: Path) -> list[dict]:
    """Parse a raw facility JSON file and return a list of facility dicts."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with file_path.open() as fh:
        data = json.load(fh)

    # Normalise: accept both a bare list or {"facilities": [...]}
    if isinstance(data, list):
        records = data
    elif isinstance(data, dict) and "facilities" in data:
        records = data["facilities"]
    else:
        raise ValueError("Unexpected JSON shape — expected list or {facilities: [...]}")

    logger.info("Loaded %d facilities from %s", len(records), file_path)
    return records


def ingest(records: list[dict]) -> None:
    """Placeholder: insert/upsert records into Postgres via SQLAlchemy."""
    # TODO: wire up SQLAlchemy session and upsert logic
    for record in records:
        logger.debug("Would insert: %s", record.get("id", "<no-id>"))
    logger.info("Ingested %d records (dry-run)", len(records))


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Load facility JSON into Postgres")
    parser.add_argument("--file", required=True, type=Path, help="Path to JSON file")
    args = parser.parse_args()

    records = load_facilities(args.file)
    ingest(records)


if __name__ == "__main__":
    main()
