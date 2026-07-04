"""
flag_facilities.py — Evaluate facility operational risk metrics and flag high-risk facilities.

Evaluates 5 inputs:
1. Stock-out frequency (> 20.0% is flagged)
2. Bed volatility (occupancy rate standard deviation > 0.30 is flagged)
3. Doctor attendance (< 80.0% is flagged)
4. Footfall-vs-median (median count / overall median < 0.50 is flagged)
5. Test gap percentage (> 30.0% is flagged)
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

# ─── Path bootstrap — reuse backend ORM models ───────────────────────────────
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# ─── Load Environment Variables BEFORE Importing App Modules ───
from dotenv import load_dotenv
load_dotenv(backend_dir / ".env")
load_dotenv(backend_dir.parent / ".env")

import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ai.audit_tests import get_test_gaps
from app.models.bed import Bed
from app.models.facility import Facility
from app.models.footfall import FootfallLog
from app.models.inventory import StockLevel
from app.models.staff import AttendanceLog, Staff


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


def calculate_stockout_frequency(session: Session, facility_id: Any) -> float:
    """Calculate stockout frequency as the percentage of inventory items currently out of stock (quantity <= 0).

    Returns percentage between 0.0 and 100.0.
    """
    levels = session.query(StockLevel).filter(StockLevel.facility_id == facility_id).all()
    if not levels:
        return 0.0
    stockout_count = sum(1 for lvl in levels if float(lvl.quantity) <= 0)
    return (stockout_count / len(levels)) * 100.0


def calculate_bed_volatility(session: Session, facility_id: Any) -> float:
    """Calculate bed volatility as the standard deviation of bed occupancy rates.

    Occupancy Rate = occupied_beds / total_beds.
    Returns standard deviation (0.0 to 1.0).
    """
    bed_records = (
        session.query(Bed)
        .filter(Bed.facility_id == facility_id)
        .order_by(Bed.updated_at.asc())
        .all()
    )
    if len(bed_records) < 2:
        return 0.0

    rates = []
    for record in bed_records:
        total = record.total_beds
        occupied = record.occupied_beds
        rates.append(occupied / total if total > 0 else 0.0)

    return float(np.std(rates))


def calculate_doctor_attendance(session: Session, facility_id: Any) -> float:
    """Calculate doctor attendance rate as percentage of days present.

    Considers staff roles containing 'doctor' or 'medical officer' case-insensitively.
    Returns percentage between 0.0 and 100.0 (defaults to 100.0 if no doctors exist).
    """
    doctor_staff = (
        session.query(Staff)
        .filter(
            Staff.facility_id == facility_id,
            Staff.role.ilike("%doctor%") | Staff.role.ilike("%medical officer%"),
        )
        .all()
    )
    if not doctor_staff:
        return 100.0

    doc_ids = [doc.id for doc in doctor_staff]
    logs = (
        session.query(AttendanceLog)
        .filter(AttendanceLog.staff_id.in_(doc_ids))
        .all()
    )
    if not logs:
        return 100.0

    present_count = sum(1 for log in logs if log.present)
    return (present_count / len(logs)) * 100.0


def calculate_facility_median_footfall(session: Session, facility_id: Any) -> float:
    """Calculate the median daily patient count for whole-facility logs (department=None)."""
    logs = (
        session.query(FootfallLog)
        .filter(
            FootfallLog.facility_id == facility_id,
            FootfallLog.department == None,
        )
        .all()
    )
    if not logs:
        return 0.0
    counts = [log.patient_count for log in logs]
    return float(np.median(counts))


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
            print("No facilities found. Please seed the database first.")
            return

        # 1. Fetch test gap percentages
        test_gaps = get_test_gaps(session)

        # 2. Calculate median footfalls to compute overall median
        facility_medians = {}
        for facility in facilities:
            facility_medians[facility.id] = calculate_facility_median_footfall(session, facility.id)

        valid_medians = [m for m in facility_medians.values() if m > 0]
        overall_median = float(np.median(valid_medians)) if valid_medians else 0.0

        # 3. Compile report
        report_data = []
        for facility in facilities:
            stockout_freq = calculate_stockout_frequency(session, facility.id)
            bed_vol = calculate_bed_volatility(session, facility.id)
            doc_att = calculate_doctor_attendance(session, facility.id)
            
            # Footfall comparison
            fac_median = facility_medians[facility.id]
            footfall_ratio = fac_median / overall_median if overall_median > 0 else 1.0
            
            test_gap = test_gaps.get(facility.id, 0.0)

            # Flagging criteria
            flags = []
            if stockout_freq > 20.0:
                flags.append("Stockouts (>20%)")
            if bed_vol > 0.30:
                flags.append("Bed Volatility (>0.30)")
            if doc_att < 80.0:
                flags.append("Doctor Attendance (<80%)")
            if footfall_ratio < 0.50:
                flags.append("Footfall-vs-Median (<0.50)")
            if test_gap > 30.0:
                flags.append("Diagnostic Gap (>30%)")

            is_flagged = len(flags) > 0

            report_data.append({
                "facility_id": facility.facility_id,
                "name": facility.name,
                "tier": facility.tier.value if hasattr(facility.tier, "value") else str(facility.tier),
                "stockout_frequency": stockout_freq,
                "bed_volatility": bed_vol,
                "doctor_attendance": doc_att,
                "footfall_vs_median": footfall_ratio,
                "test_gap_percentage": test_gap,
                "flagged": is_flagged,
                "flagged_reasons": flags
            })

        # ─── Print Report ──────────────────────────────────────────────────────
        print("=" * 115)
        print(f"{'FACILITY OPERATIONAL RISK ASSESSMENT REPORT':^115}")
        print("=" * 115)
        header = f"{'ID':<12} | {'Name':<22} | {'Stockout%':<9} | {'BedVol':<6} | {'DocAtt%':<8} | {'Footfall/Med':<12} | {'TestGap%':<8} | {'Status':<10}"
        print(header)
        print("-" * 115)

        for r in report_data:
            status = "⚠️ FLAGGED" if r["flagged"] else "✅ OK"
            row = (
                f"{r['facility_id']:<12} | "
                f"{r['name'][:22]:<22} | "
                f"{r['stockout_frequency']:6.1f}% | "
                f"{r['bed_volatility']:6.3f} | "
                f"{r['doctor_attendance']:7.1f}% | "
                f"{r['footfall_vs_median']:12.2f} | "
                f"{r['test_gap_percentage']:7.1f}% | "
                f"{status:<10}"
            )
            print(row)
            if r["flagged"]:
                print(f"   ↳ Reasons: {', '.join(r['flagged_reasons'])}")

        print("=" * 115)

        # ─── Save to JSON ──────────────────────────────────────────────────────
        output_file = backend_dir / "ai" / "flagged_facilities.json"
        with output_file.open("w") as fh:
            json.dump({
                "overall_median_footfall": overall_median,
                "facilities": report_data
            }, fh, indent=2)
        print(f"Saved risk report to {output_file.resolve()}")

    except Exception as exc:
        print(f"Error executing facility flagging: {exc}", file=sys.stderr)
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
