"""
generator.py — Generate synthetic / placeholder facility JSON fixtures.

Usage:
    python -m data_pipeline.scripts.generator --count 50 --out research/facilities_sample.json
"""
from __future__ import annotations

import argparse
import json
import logging
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

_FACILITY_TYPES = ["hospital", "clinic", "pharmacy", "diagnostic_centre", "nursing_home"]
_STATES = ["AN", "AP", "AR", "AS", "BR", "CG", "DL", "GA", "GJ", "HR"]


def generate_facility(index: int) -> dict:
    """Return a single synthetic facility record."""
    return {
        "id": str(uuid.uuid4()),
        "name": f"Medico Facility #{index:04d}",
        "type": _FACILITY_TYPES[index % len(_FACILITY_TYPES)],
        "state": _STATES[index % len(_STATES)],
        "address": f"{index * 7} Main Road, City",
        "pincode": f"{600000 + index:06d}",
        "phone": f"+91-98{index:08d}",
        "active": True,
    }


def generate(count: int, out_path: Path) -> None:
    records = [generate_facility(i) for i in range(1, count + 1)]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as fh:
        json.dump({"facilities": records}, fh, indent=2)
    logger.info("Wrote %d facility records to %s", count, out_path)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Generate synthetic facility fixtures")
    parser.add_argument("--count", type=int, default=10, help="Number of records")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("research/facilities_sample.json"),
        help="Output JSON path",
    )
    args = parser.parse_args()
    generate(args.count, args.out)


if __name__ == "__main__":
    main()
