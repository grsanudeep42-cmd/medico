"""
audit_tests.py — Audit diagnostic test availability against IPHS requirements.

Calculates the missing tests and gap percentage for each facility based on its tier.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

# ─── Path bootstrap — reuse backend ORM models ───────────────────────────────
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# ─── Load Environment Variables BEFORE Importing App Modules ───
from dotenv import load_dotenv
load_dotenv(backend_dir / ".env")
load_dotenv(backend_dir.parent / ".env")

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models.facility import Facility
from app.models.test_availability import TestAvailability


def _build_engine(database_url: str):
    """Return a synchronous SQLAlchemy engine, trying port 5432 then 5433."""
    sync_url = re.sub(r"^postgresql\+asyncpg", "postgresql+psycopg2", database_url)
    candidates = [sync_url, re.sub(r":5432/", ":5433/", sync_url)]

    for url in candidates:
        try:
            engine = create_engine(url, connect_args={"connect_timeout": 5})
            with engine.connect():
                pass  # validate connection
            return engine
        except Exception:
            continue
    return None


def calculate_facility_gap(
    facility: Facility, available_tests: Set[str]
) -> Tuple[List[str], float]:
    """Calculate the missing tests and gap percentage for a single facility.

    Returns (missing_tests_list, gap_percentage).
    """
    tier_name = facility.tier.value if hasattr(facility.tier, "value") else str(facility.tier)
    required_tests = settings.required_tests_by_tier.get(tier_name, [])

    if not required_tests:
        return [], 0.0

    missing_tests = [test for test in required_tests if test not in available_tests]
    gap_percentage = (len(missing_tests) / len(required_tests)) * 100.0
    return missing_tests, gap_percentage


def get_test_gaps(session: Session) -> Dict[object, float]:
    """Retrieve test gap percentages for all facilities.

    Returns a dictionary mapping facility.id (UUID) to test_gap_percentage (float).
    """
    facilities = session.query(Facility).all()
    gaps = {}

    for facility in facilities:
        # Get tests currently marked available=True for this facility
        avail_rows = (
            session.query(TestAvailability)
            .filter(
                TestAvailability.facility_id == facility.id,
                TestAvailability.available == True,
            )
            .all()
        )
        avail_set = {row.test_name for row in avail_rows}
        _, gap_pct = calculate_facility_gap(facility, avail_set)
        gaps[facility.id] = gap_pct

    return gaps


def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    engine = _build_engine(database_url)
    if engine is None:
        print("Could not connect to the database.", file=sys.stderr)
        sys.exit(1)

    SessionFactory = sessionmaker(bind=engine)
    session = SessionFactory()

    try:
        facilities = session.query(Facility).all()
        if not facilities:
            print("No facilities found in the database. Run loader or seeder first.")
            return

        print("=" * 80)
        print(f"{'FACILITY DIAGNOSTIC TEST AUDIT (IPHS STANDARDS)':^80}")
        print("=" * 80)

        for facility in facilities:
            # Query available tests
            avail_rows = (
                session.query(TestAvailability)
                .filter(
                    TestAvailability.facility_id == facility.id,
                    TestAvailability.available == True,
                )
                .all()
            )
            avail_set = {row.test_name for row in avail_rows}

            tier_name = facility.tier.value if hasattr(facility.tier, "value") else str(facility.tier)
            required = settings.required_tests_by_tier.get(tier_name, [])
            missing, gap_pct = calculate_facility_gap(facility, avail_set)

            print(f"Facility: {facility.name} ({facility.facility_id})")
            print(f"  Tier: {tier_name} | Type: {facility.facility_type.value}")
            print(f"  Required Tests ({len(required)}): {', '.join(required) if required else 'None'}")
            print(f"  Available Tests ({len(avail_set)}): {', '.join(avail_set) if avail_set else 'None'}")
            if missing:
                print(f"  Missing Tests ({len(missing)}): {', '.join(missing)}")
            else:
                print("  Missing Tests: None (100% Compliant)")
            print(f"  Diagnostic Gap: {gap_pct:.2f}%")
            print("-" * 80)

    except Exception as exc:
        print(f"Error executing diagnostic audit: {exc}", file=sys.stderr)
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
