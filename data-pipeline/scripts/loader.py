"""
loader.py — Load raw facility JSON files from /research into Postgres.

Usage:
    python -m data_pipeline.scripts.loader --file research/facilities_state_2024-01-01.json
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add backend directory to sys.path to reuse ORM models
backend_dir = Path(__file__).resolve().parents[2] / "backend"
sys.path.append(str(backend_dir))

# Set up logging early
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("loader")

# Load environment
from dotenv import load_dotenv
env_loaded = False
for p in [Path("."), Path(".."), Path("../.."), backend_dir]:
    env_path = p / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        env_loaded = True
        logger.info("Loaded environment from %s", env_path.resolve())
        break

if not env_loaded:
    logger.warning("No .env file found; using existing environment variables.")

from app.models.facility import Facility, FacilityTier, FacilityType
from app.models.department import Department
from app.models.equipment import Equipment
from app.models.daily_average import DailyAverage

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session


def parse_datetime(dt_str: str | None) -> datetime:
    """Parse datetime string to timezone-aware datetime, default to current UTC time."""
    if not dt_str:
        return datetime.now(timezone.utc)
    try:
        if dt_str.endswith("Z"):
            dt_str = dt_str[:-1] + "+00:00"
        return datetime.fromisoformat(dt_str)
    except Exception:
        logger.warning("Failed to parse datetime '%s', defaulting to current time", dt_str)
        return datetime.now(timezone.utc)


def load_facilities(file_path: Path) -> list[dict]:
    """Parse a raw facility JSON file and return a list of facility dicts."""
    if not file_path.exists():
        # Try relative paths
        pipeline_root = Path(__file__).resolve().parents[1]
        alt_path = pipeline_root / file_path
        if alt_path.exists():
            file_path = alt_path
        else:
            workspace_root = Path(__file__).resolve().parents[2]
            alt_path2 = workspace_root / file_path
            if alt_path2.exists():
                file_path = alt_path2
            else:
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


def ingest(records: list[dict], session: Session) -> None:
    """Insert/upsert facility records into Postgres via SQLAlchemy."""
    for record in records:
        # Validate schema
        required_fields = ["facility_id", "name", "facility_type", "tier"]
        for field in required_fields:
            if not record.get(field):
                raise ValueError(f"Missing required field '{field}' in record: {record}")

        facility_id = record["facility_id"]
        name = record["name"]
        fac_type = record["facility_type"]
        tier = record["tier"]
        capacity = record.get("capacity", 0)
        address = record.get("address", "Not Specified")
        lat = record.get("lat", 0.0)
        lng = record.get("lng", 0.0)

        # Validate enums
        try:
            FacilityType(fac_type)
        except ValueError:
            raise ValueError(f"Invalid facility_type: '{fac_type}'. Must be PHC, CHC, or tertiary_referral")

        try:
            FacilityTier(tier)
        except ValueError:
            raise ValueError(f"Invalid tier: '{tier}'. Must be primary, community, or apex")

        # Validate daily_averages source_url
        daily_averages_data = record.get("daily_averages", [])
        for da in daily_averages_data:
            if not da.get("source_url") or not str(da["source_url"]).strip():
                raise ValueError(f"Daily average entry for metric '{da.get('metric_name', 'unknown')}' in facility '{facility_id}' lacks source_url citation.")

        # Idempotency: Delete existing facility
        existing = session.query(Facility).filter(Facility.facility_id == facility_id).first()
        if existing:
            logger.info("Facility '%s' already exists. Deleting old record for idempotency...", facility_id)
            session.delete(existing)
            session.flush()

        # Insert new facility
        facility = Facility(
            facility_id=facility_id,
            name=name,
            facility_type=FacilityType(fac_type),
            tier=FacilityTier(tier),
            address=address,
            lat=lat,
            lng=lng,
            sanctioned_beds=capacity,
            functional_beds_estimate=capacity
        )
        session.add(facility)
        session.flush()

        # Insert departments
        departments_data = record.get("departments", [])
        for dept in departments_data:
            dept_name = dept if isinstance(dept, str) else dept.get("name")
            if dept_name:
                db_dept = Department(name=dept_name, facility_id=facility.id)
                session.add(db_dept)

        # Insert equipment
        equipment_data = record.get("equipment", [])
        for equip in equipment_data:
            if isinstance(equip, str):
                equip_name = equip
                equip_cat = "General"
            else:
                equip_name = equip.get("name")
                equip_cat = equip.get("category", "General")
            if equip_name:
                db_equip = Equipment(name=equip_name, category=equip_cat, facility_id=facility.id)
                session.add(db_equip)

        # Insert daily averages
        for da in daily_averages_data:
            db_da = DailyAverage(
                facility_id=facility.id,
                metric_name=da["metric_name"],
                avg_value=da["avg_value"],
                min_value=da.get("min_value"),
                max_value=da.get("max_value"),
                source_url=da["source_url"],
                recorded_at=parse_datetime(da.get("recorded_at"))
            )
            session.add(db_da)

        logger.info("Ingested facility: %s (%s)", name, facility_id)


def main() -> None:
    parser = argparse.ArgumentParser(description="Load facility JSON into Postgres")
    parser.add_argument("--file", required=True, type=Path, help="Path to JSON file")
    args = parser.parse_args()

    # Get database URL and normalize it for sync psycopg2 connection
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable is not set!")
        sys.exit(1)

    sync_url = re.sub(r"^postgresql\+asyncpg", "postgresql+psycopg2", database_url)
    
    # Try connecting. If it uses port 5432 and fails, try 5433 (host port mapping fallback)
    engine = None
    for url in [sync_url, re.sub(r":5432/", ":5433/", sync_url)]:
        try:
            logger.info("Attempting to connect to DB: %s", re.sub(r":[^/@:]+@", ":***@", url))
            engine = create_engine(url, connect_args={"connect_timeout": 3})
            # Test connection
            with engine.connect() as conn:
                pass
            sync_url = url
            break
        except Exception as e:
            logger.warning("Failed to connect to %s: %s", re.sub(r":[^/@:]+@", ":***@", url), e)
            engine = None

    if not engine:
        logger.error("Could not connect to the database! Make sure the Postgres container is running.")
        sys.exit(1)

    # Establish session
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        records = load_facilities(args.file)
        ingest(records, session)
        session.commit()
        logger.info("Successfully committed transaction.")
    except Exception as e:
        session.rollback()
        logger.error("Transaction rolled back due to error: %s", e)
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()
