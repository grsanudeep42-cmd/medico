"""Router for AI-driven facility metrics risk assessment, demand forecasting, and resource redistribution."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
import numpy as np

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings
from app.models.facility import Facility
from app.models.bed import Bed
from app.models.staff import Staff, AttendanceLog
from app.models.footfall import FootfallLog
from app.models.inventory import StockLevel, InventoryItem, StockTransaction, TransactionType
from app.models.test_availability import TestAvailability

router = APIRouter(prefix="/ai", tags=["ai"])


def calculate_facility_gap(facility: Facility, available_tests: set[str]) -> float:
    """Calculate the missing tests and gap percentage for a single facility."""
    tier_name = facility.tier.value if hasattr(facility.tier, "value") else str(facility.tier)
    required_tests = settings.required_tests_by_tier.get(tier_name, [])

    if not required_tests:
        return 0.0

    missing_tests = [test for test in required_tests if test not in available_tests]
    return (len(missing_tests) / len(required_tests)) * 100.0


@router.get("/analytics")
async def get_ai_analytics(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Dynamically evaluate risk flags, demand forecasts, and redistribution recommendations."""
    # 1. Fetch facilities
    fac_result = await db.execute(select(Facility))
    facilities = list(fac_result.scalars().all())
    if not facilities:
        return {
            "overall_median_footfall": 0.0,
            "facilities": [],
            "demand_forecasts": [],
            "redistribution_recommendations": []
        }

    # 2. Gather footfall medians to calculate overall median
    facility_medians: Dict[uuid.UUID, float] = {}
    for facility in facilities:
        ff_result = await db.execute(
            select(FootfallLog)
            .where(FootfallLog.facility_id == facility.id, FootfallLog.department == None)
        )
        logs = ff_result.scalars().all()
        if logs:
            counts = [log.patient_count for log in logs]
            facility_medians[facility.id] = float(np.median(counts))
        else:
            facility_medians[facility.id] = 0.0

    valid_medians = [m for m in facility_medians.values() if m > 0]
    overall_median = float(np.median(valid_medians)) if valid_medians else 0.0

    # 3. Process facilities risk flags
    facility_reports = []
    at_risk_facilities = []
    
    for facility in facilities:
        # Stockouts
        stock_result = await db.execute(
            select(StockLevel).where(StockLevel.facility_id == facility.id)
        )
        levels = list(stock_result.scalars().all())
        if levels:
            stockout_count = sum(1 for lvl in levels if float(lvl.quantity) <= 0)
            stockout_freq = (stockout_count / len(levels)) * 100.0
        else:
            stockout_freq = 0.0

        # Bed Volatility
        bed_result = await db.execute(
            select(Bed).where(Bed.facility_id == facility.id).order_by(Bed.updated_at.asc())
        )
        bed_records = list(bed_result.scalars().all())
        if len(bed_records) >= 2:
            rates = [
                rec.occupied_beds / rec.total_beds if rec.total_beds > 0 else 0.0
                for rec in bed_records
            ]
            bed_vol = float(np.std(rates))
        else:
            bed_vol = 0.0

        # Doctor Attendance
        doc_result = await db.execute(
            select(Staff)
            .where(
                Staff.facility_id == facility.id,
                func.lower(Staff.role).like("%doctor%") | func.lower(Staff.role).like("%medical officer%")
            )
        )
        doctors = list(doc_result.scalars().all())
        if doctors:
            doc_ids = [doc.id for doc in doctors]
            att_result = await db.execute(
                select(AttendanceLog).where(AttendanceLog.staff_id.in_(doc_ids))
            )
            logs = list(att_result.scalars().all())
            if logs:
                present_count = sum(1 for log in logs if log.present)
                doc_att = (present_count / len(logs)) * 100.0
            else:
                doc_att = 100.0
        else:
            doc_att = 100.0

        # Footfall comparison
        fac_median = facility_medians.get(facility.id, 0.0)
        footfall_ratio = fac_median / overall_median if overall_median > 0 else 1.0

        # Test Gap
        test_result = await db.execute(
            select(TestAvailability)
            .where(TestAvailability.facility_id == facility.id, TestAvailability.available == True)
        )
        avail_rows = test_result.scalars().all()
        avail_set = {row.test_name for row in avail_rows}
        test_gap = calculate_facility_gap(facility, avail_set)

        # Flagging
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

        report = {
            "id": str(facility.id),
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
        }
        facility_reports.append(report)
        if is_flagged:
            at_risk_facilities.append(report)

    # 4. Generate Demand Forecasts & Early Warnings
    demand_forecasts = []
    item_catalog_result = await db.execute(select(InventoryItem))
    items_by_id = {item.id: item for item in item_catalog_result.scalars().all()}

    all_stock_result = await db.execute(select(StockLevel))
    all_stock_levels = all_stock_result.scalars().all()

    for sl in all_stock_levels:
        item = items_by_id.get(sl.item_id)
        if not item:
            continue
        
        # Estimate daily rate from negative transaction history, default to 5.0 if none
        tx_result = await db.execute(
            select(StockTransaction)
            .where(
                StockTransaction.facility_id == sl.facility_id,
                StockTransaction.item_id == sl.item_id,
                StockTransaction.delta < 0
            )
            .order_by(StockTransaction.timestamp.desc())
            .limit(20)
        )
        transactions = list(tx_result.scalars().all())
        if transactions:
            total_dispensed = abs(sum(tx.delta for tx in transactions))
            # Calculate span in days
            newest = transactions[0].timestamp
            oldest = transactions[-1].timestamp
            days_span = max((newest - oldest).days, 1)
            daily_rate = max(total_dispensed / days_span, 1.0)
        else:
            daily_rate = 5.0 # default estimated consumption

        qty = float(sl.quantity)
        days_remaining = qty / daily_rate

        # Resolve facility object
        fac_obj = next((f for f in facilities if f.id == sl.facility_id), None)
        if not fac_obj:
            continue

        if days_remaining <= 7 or qty <= float(sl.reorder_threshold):
            status_level = "critical" if days_remaining <= 3 else "warning"
            demand_forecasts.append({
                "facility_id": str(sl.facility_id),
                "facility_name": fac_obj.name,
                "item_id": str(sl.item_id),
                "item_name": item.name,
                "category": item.category,
                "quantity": qty,
                "reorder_threshold": float(sl.reorder_threshold),
                "days_remaining": round(days_remaining, 1),
                "daily_rate": round(daily_rate, 1),
                "status": status_level
            })

    # Sort forecasts: critical first
    demand_forecasts.sort(key=lambda x: (x["status"] != "critical", x["days_remaining"]))

    # 5. Generate Resource Redistribution Recommendations
    redistribution_recommendations = []
    # Identify items in critical need (quantity <= threshold)
    critical_needs = [f for f in demand_forecasts if f["quantity"] <= f["reorder_threshold"]]

    for need in critical_needs:
        to_fac_id = uuid.UUID(need["facility_id"])
        item_id = uuid.UUID(need["item_id"])
        
        # Look for a surplus facility for the same item
        surplus_result = await db.execute(
            select(StockLevel)
            .where(
                StockLevel.item_id == item_id,
                StockLevel.facility_id != to_fac_id,
                StockLevel.quantity > StockLevel.reorder_threshold * 2
            )
        )
        surpluses = list(surplus_result.scalars().all())
        if surpluses:
            # Pick the one with the maximum surplus
            surpluses.sort(key=lambda s: float(s.quantity) - float(s.reorder_threshold), reverse=True)
            best_source = surpluses[0]
            
            from_fac_obj = next((f for f in facilities if f.id == best_source.facility_id), None)
            if from_fac_obj:
                surplus_qty = float(best_source.quantity) - float(best_source.reorder_threshold)
                transfer_qty = min(
                    float(need["reorder_threshold"]) - float(need["quantity"]) + 10,
                    surplus_qty * 0.5
                )
                transfer_qty = max(round(transfer_qty), 5.0)

                redistribution_recommendations.append({
                    "id": str(uuid.uuid4()),
                    "from_facility_id": str(best_source.facility_id),
                    "from_facility_name": from_fac_obj.name,
                    "to_facility_id": need["facility_id"],
                    "to_facility_name": need["facility_name"],
                    "item_id": need["item_id"],
                    "item_name": need["item_name"],
                    "recommended_quantity": transfer_qty,
                    "reason": f"To resolve critical shortage (current qty: {need['quantity']}, reorder threshold: {need['reorder_threshold']})"
                })

    return {
        "overall_median_footfall": overall_median,
        "facilities": facility_reports,
        "at_risk_facilities": at_risk_facilities,
        "demand_forecasts": demand_forecasts,
        "redistribution_recommendations": redistribution_recommendations[:10]  # limit to top 10 recommendations
    }
