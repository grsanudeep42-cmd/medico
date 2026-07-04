"""
generator.py — Generate synthetic facility JSON fixtures matching the database schema.

Usage:
    python -m data_pipeline.scripts.generator --count 50 --out research/facilities_sample.json
"""
from __future__ import annotations

import argparse
import json
import logging
import random
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

_DEPARTMENTS_BY_TYPE = {
    "PHC": ["General Medicine", "Pediatrics"],
    "CHC": ["General Medicine", "Pediatrics", "General Surgery", "Obstetrics & Gynecology"],
    "tertiary_referral": ["General Medicine", "Pediatrics", "General Surgery", "Obstetrics & Gynecology", "Cardiology", "Neurology", "Oncology"]
}

_EQUIPMENT_BY_TYPE = [
    {"name": "Basic ECG Monitor", "category": "Diagnostics"},
    {"name": "Refrigerator", "category": "Cold Chain"},
    {"name": "X-Ray Machine", "category": "Diagnostics"},
    {"name": "Ventilator", "category": "Critical Care"},
    {"name": "Centrifuge", "category": "Laboratory"}
]


def generate_facility(index: int) -> dict:
    """Return a single schema-compliant facility record with nested dependencies."""
    # Pick type and matching tier
    fac_types = ["PHC", "CHC", "tertiary_referral"]
    fac_tiers = ["primary", "community", "apex"]
    
    type_idx = index % len(fac_types)
    fac_type = fac_types[type_idx]
    tier = fac_tiers[type_idx]
    
    # Capacity base on tier
    if tier == "primary":
        capacity = random.randint(10, 30)
        avg_visits = float(random.randint(25, 60))
    elif tier == "community":
        capacity = random.randint(40, 90)
        avg_visits = float(random.randint(70, 150))
    else:
        capacity = random.randint(120, 250)
        avg_visits = float(random.randint(180, 450))

    facility_id = f"FAC-{index:04d}"
    
    # Generate departments
    depts = _DEPARTMENTS_BY_TYPE[fac_type]
    
    # Generate equipment
    eq_count = random.randint(1, len(_EQUIPMENT_BY_TYPE))
    equipment = random.sample(_EQUIPMENT_BY_TYPE, eq_count)

    # Generate daily averages
    daily_averages = [
        {
            "metric_name": "outpatient_visits",
            "avg_value": avg_visits,
            "min_value": float(round(avg_visits * 0.6, 1)),
            "max_value": float(round(avg_visits * 1.5, 1)),
            "source_url": "https://gov.in/stats/2024/report.pdf",
            "recorded_at": "2024-06-15T08:00:00Z"
        },
        {
            "metric_name": "bed_occupancy_rate",
            "avg_value": float(round(random.uniform(0.4, 0.8), 2)),
            "source_url": "https://gov.in/stats/2024/report.pdf",
            "recorded_at": "2024-06-15T08:00:00Z"
        }
    ]

    return {
        "facility_id": facility_id,
        "name": f"Medico {fac_type} {index:04d}",
        "facility_type": fac_type,
        "tier": tier,
        "capacity": capacity,
        "address": f"{index * 7} Main Road, Block-{index % 5 + 1}, District",
        "lat": float(round(random.uniform(15.0, 20.0), 5)),
        "lng": float(round(random.uniform(73.0, 78.0), 5)),
        "departments": depts,
        "equipment": equipment,
        "daily_averages": daily_averages
    }


def generate(count: int, out_path: Path) -> None:
    records = [generate_facility(i) for i in range(1, count + 1)]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as fh:
        json.dump({"facilities": records}, fh, indent=2)
    logger.info("Wrote %d facility records to %s", count, out_path)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Generate schema-compliant facility fixtures")
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
