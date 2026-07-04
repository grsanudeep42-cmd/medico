"""
load_facility.py — Load a facility JSON file into Postgres.

CLI:
    python load_facility.py research/<file>.json
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
logger = logging.getLogger("load_facility")

# ─── Load Environment Variables BEFORE Importing App Modules ───
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

# Now we can safely import the database and models because the environment is loaded
from app.models.facility import Facility, FacilityTier, FacilityType
from app.models.department import Department
from app.models.equipment import Equipment
from app.models.daily_average import DailyAverage

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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

def main() -> None:
    parser = argparse.ArgumentParser(description="Load facility JSON into Postgres")
    parser.add_argument("file", help="Path to JSON file")
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

    # Find the JSON file
    file_path = Path(args.file)
    if not file_path.exists():
        # Try relative to the data-pipeline directory
        pipeline_root = Path(__file__).resolve().parents[1]
        alt_path = pipeline_root / args.file
        if alt_path.exists():
            file_path = alt_path
        else:
            # Try relative to workspace root
            workspace_root = Path(__file__).resolve().parents[2]
            alt_path2 = workspace_root / args.file
            if alt_path2.exists():
                file_path = alt_path2
            else:
                logger.error("JSON file not found: %s", args.file)
                sys.exit(1)

    logger.info("Reading facility JSON from: %s", file_path.resolve())
    with file_path.open() as f:
        try:
            data = json.load(f)
        except Exception as e:
            logger.error("Failed to parse JSON file: %s", e)
            sys.exit(1)

    # Validate JSON Schema requirements
    required_fields = ["facility_id", "name", "facility_type", "tier"]
    for field in required_fields:
        if not data.get(field):
            logger.error("Missing required top-level field: %s", field)
            sys.exit(1)

    # 1. Reject if daily_averages is present and any entry is missing source_url
    daily_averages_data = data.get("daily_averages", [])
    if not isinstance(daily_averages_data, list):
        logger.error("daily_averages must be a list of objects")
        sys.exit(1)

    for da in daily_averages_data:
        if not da.get("source_url") or not str(da["source_url"]).strip():
            logger.error("Validation failed: daily_averages entry is missing required 'source_url' field! Aborting.")
            # Fail loudly rather than insert unsourced numbers
            raise ValueError(f"Validation failed: Daily average entry for metric '{da.get('metric_name', 'unknown')}' lacks source_url citation.")

    # 2. Extract fields
    facility_id = data["facility_id"]
    name = data["name"]
    fac_type = data["facility_type"]
    tier = data["tier"]
    capacity = data.get("capacity", 0)
    
    # Address, lat, lng fallback
    address = data.get("address", "Not Specified")
    lat = data.get("lat", 0.0)
    lng = data.get("lng", 0.0)

    # Check for enum validity
    try:
        FacilityType(fac_type)
    except ValueError:
        logger.error("Invalid facility_type: '%s'. Must be one of: PHC, CHC, tertiary_referral", fac_type)
        sys.exit(1)

    try:
        FacilityTier(tier)
    except ValueError:
        logger.error("Invalid tier: '%s'. Must be one of: primary, community, apex", tier)
        sys.exit(1)

    # Establish session
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Idempotency: Delete existing facility (and all cascaded relations) if facility_id matches
        existing = session.query(Facility).filter(Facility.facility_id == facility_id).first()
        if existing:
            logger.info("Facility with facility_id '%s' already exists. Deleting old record for idempotency...", facility_id)
            session.delete(existing)
            session.commit()

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
        session.flush() # Populate facility.id

        # Insert departments
        departments_data = data.get("departments", [])
        for dept in departments_data:
            dept_name = dept if isinstance(dept, str) else dept.get("name")
            if dept_name:
                db_dept = Department(name=dept_name, facility_id=facility.id)
                session.add(db_dept)

        # Insert equipment
        equipment_data = data.get("equipment", [])
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

        session.commit()
        logger.info("Successfully loaded facility '%s' (%s) into database.", name, facility_id)

    except Exception as e:
        session.rollback()
        logger.error("Transaction rolled back due to error: %s", e)
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main()
