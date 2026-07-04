"""
seed_test_data.py — Seed the database with operational mock data.

Generates testing logs for:
- inventory_items + stock_levels (to test stock-out frequency)
- test_availability (to test diagnostic gap %)
- beds (to test bed occupancy volatility)
- staff + attendance_logs (to test doctor attendance rate)
- footfall_logs (to test median footfall ratio)
"""
from __future__ import annotations

import logging
import os
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parents[2] / "backend"
sys.path.append(str(backend_dir))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_test_data")

from dotenv import load_dotenv
load_dotenv(backend_dir / ".env")
load_dotenv(backend_dir.parent / ".env")

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.bed import Bed
from app.models.facility import Facility
from app.models.footfall import FootfallLog
from app.models.inventory import InventoryItem, StockLevel
from app.models.staff import AttendanceLog, Staff
from app.models.test_availability import TestAvailability


def _build_engine(database_url: str):
    """Return a synchronous SQLAlchemy engine, trying port 5432 then 5433."""
    sync_url = re.sub(r"^postgresql\+asyncpg", "postgresql+psycopg2", database_url)
    candidates = [sync_url, re.sub(r":5432/", ":5433/", sync_url)]

    for url in candidates:
        try:
            engine = create_engine(url, connect_args={"connect_timeout": 3})
            with engine.connect():
                pass
            return engine
        except Exception:
            continue
    return None


def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable is not set!")
        sys.exit(1)

    engine = _build_engine(database_url)
    if not engine:
        logger.error("Could not connect to the database!")
        sys.exit(1)

    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Clear existing seeded operational tables for idempotency
        logger.info("Cleaning up old operational mock data...")
        session.execute(text("TRUNCATE TABLE test_availability, beds, attendance_logs, staff, stock_transactions, stock_levels, inventory_items, footfall_logs CASCADE"))
        session.commit()

        facilities = session.query(Facility).all()
        if not facilities:
            logger.error("No facilities found! Run load_facility.py first to load basic facilities.")
            sys.exit(1)

        logger.info("Seeding inventory items...")
        items = [
            InventoryItem(name="Paracetamol", category="Essential Medicine", unit="tablets"),
            InventoryItem(name="Amoxicillin", category="Essential Medicine", unit="tablets"),
            InventoryItem(name="Rapid Malaria Test Kit", category="Reagent", unit="kits"),
            InventoryItem(name="Disposable Syringe", category="Consumable", unit="pieces"),
        ]
        session.add_all(items)
        session.flush()

        # Let's seed per facility
        now = datetime.now(timezone.utc)
        today = date.today()

        for fac in facilities:
            logger.info("Seeding data for facility '%s' (%s, %s)...", fac.name, fac.facility_id, fac.tier.value)

            # 1. Seed Stock Levels
            # General Hospital PHC (FAC-001): 50% stock-out (2 out of 4)
            # Cardiology Facility (FAC-d6347b6c): 0% stock-out (0 out of 4)
            # Test Primary Health Centre (TEST-FAC-100): 25% stock-out (1 out of 4)
            for idx, item in enumerate(items):
                qty = 50.0
                if fac.facility_id == "FAC-001":
                    if idx in (0, 2):  # Paracetamol and Malaria kit stocked out
                        qty = 0.0
                elif fac.facility_id == "TEST-FAC-100":
                    if idx == 3:  # Disposable Syringe stocked out
                        qty = 0.0
                elif fac.facility_id == "FAC-d6347b6c":
                    qty = 100.0

                lvl = StockLevel(
                    facility_id=fac.id,
                    item_id=item.id,
                    quantity=qty,
                    reorder_threshold=10.0,
                    last_updated=now
                )
                session.add(lvl)

            # 2. Seed Test Availability
            # required_tests_by_tier:
            # - primary: Hb, urine routine, blood sugar, malaria smear
            # - community/apex: Hb, urine routine, blood sugar, malaria smear, X-ray, ECG, wider pathology panel
            #
            # General Hospital PHC (FAC-001): missing 2 out of 4 (50% gap)
            # Cardiology Facility (FAC-d6347b6c): missing 0 out of 7 (0% gap)
            # Test Primary Health Centre (TEST-FAC-100): missing 1 out of 4 (25% gap)
            tier_name = fac.tier.value if hasattr(fac.tier, "value") else str(fac.tier)
            required = settings.required_tests_by_tier.get(tier_name, [])
            for idx, test in enumerate(required):
                available = True
                if fac.facility_id == "FAC-001":
                    if idx in (2, 3):  # blood sugar, malaria smear unavailable
                        available = False
                elif fac.facility_id == "TEST-FAC-100":
                    if idx == 0:  # Hb unavailable
                        available = False

                t_avail = TestAvailability(
                    facility_id=fac.id,
                    test_name=test,
                    available=available,
                    last_checked=now
                )
                session.add(t_avail)

            # 3. Seed Bed Occupancy Snapshots (5 snapshots to test volatility)
            # Occupancy Rate = occupied_beds / total_beds
            # General Hospital PHC (FAC-001): total=25, occupancy = [12, 13, 11, 14, 13] -> mean ~0.50, low vol
            # Cardiology Facility (FAC-d6347b6c): total=100, occupancy = [80, 20, 90, 10, 85] -> highly volatile, std > 0.30
            # Test Primary Health Centre (TEST-FAC-100): total=25, occupancy = [5, 6, 5, 5, 6] -> low vol
            total_beds = 100 if fac.facility_id == "FAC-d6347b6c" else 25
            occupancies = [5, 6, 5, 5, 6]
            if fac.facility_id == "FAC-001":
                occupancies = [12, 13, 11, 14, 13]
            elif fac.facility_id == "FAC-d6347b6c":
                occupancies = [80, 20, 90, 10, 85]

            for offset, occ in enumerate(occupancies):
                bed_snap = Bed(
                    facility_id=fac.id,
                    total_beds=total_beds,
                    occupied_beds=occ,
                    updated_at=now - timedelta(days=offset)
                )
                session.add(bed_snap)

            # 4. Seed Staff + Doctor Attendance (last 10 days)
            # General Hospital PHC (FAC-001): Medical Officer present 9/10 days (90% attendance)
            # Cardiology Facility (FAC-d6347b6c): Medical Officer present 7/10 days (70% attendance, flagged)
            # Test Primary Health Centre (TEST-FAC-100): Medical Officer present 10/10 days (100% attendance)
            doc = Staff(
                facility_id=fac.id,
                role="Medical Officer",
                name=f"Dr. Smith at {fac.name}",
                sanctioned=True
            )
            session.add(doc)
            session.flush()

            for d_offset in range(10):
                log_date = today - timedelta(days=d_offset)
                present = True
                if fac.facility_id == "FAC-001" and d_offset == 3:
                    present = False
                elif fac.facility_id == "FAC-d6347b6c" and d_offset in (2, 5, 8):
                    present = False

                att_log = AttendanceLog(
                    staff_id=doc.id,
                    date=log_date,
                    present=present,
                    is_simulated=True,
                    basis="Monte-Carlo seed data"
                )
                session.add(att_log)

            # 5. Seed Footfall Logs (last 15 days)
            # General Hospital PHC (FAC-001): counts around 50 (median ~50)
            # Cardiology Facility (FAC-d6347b6c): counts around 120 (median ~120)
            # Test Primary Health Centre (TEST-FAC-100): counts around 15 (median ~15)
            # Overall medians: median([50, 120, 15]) = 50.0
            # Test PHC ratio = 15/50 = 0.30 (< 0.50, flagged)
            base_count = 50
            if fac.facility_id == "FAC-d6347b6c":
                base_count = 120
            elif fac.facility_id == "TEST-FAC-100":
                base_count = 15

            # We use varying counts to avoid standard deviations being exactly zero
            # range is from base_count - 5 to base_count + 5
            for f_offset in range(15):
                log_date = today - timedelta(days=f_offset)
                patient_count = base_count + (f_offset % 5 - 2)
                footfall = FootfallLog(
                    facility_id=fac.id,
                    date=log_date,
                    patient_count=patient_count,
                    department=None,
                    is_simulated=True,
                    basis="Seeded mock daily count"
                )
                session.add(footfall)

        session.commit()
        logger.info("Successfully seeded database with operational mock data.")

    except Exception as e:
        session.rollback()
        logger.error("Transaction rolled back due to error: %s", e)
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
