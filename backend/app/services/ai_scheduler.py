"""AI Scheduler — background service that evaluates facility risk automatically.

Runs every 6 hours (configurable) using APScheduler's AsyncIOScheduler.
On each run it:
  1. Runs the same analytics logic as /ai/analytics
  2. Compares newly detected conditions against existing unacknowledged alerts
  3. Only inserts a NEW alert if one for the same facility + category doesn't
     already exist and is unacknowledged (avoids alert storm / duplicates)
  4. Publishes each new alert over Redis so the dashboard WebSocket gets it
     instantly without polling

Stock-out trigger:
  check_facility_stockouts() can be called inline from the stock router on
  every stock level write — it runs fast (single-facility only).
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import numpy as np
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.alert import AlertCategory, AlertSeverity, FacilityAlert
from app.models.bed import Bed
from app.models.facility import Facility
from app.models.footfall import FootfallLog
from app.models.inventory import InventoryItem, StockLevel, StockTransaction
from app.models.staff import AttendanceLog, Staff
from app.models.test_availability import TestAvailability
from app.redis_client import get_redis
from app.services.publisher import publish

log = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None

# ── Threshold constants (mirror ai.py) ────────────────────────────────────────

STOCKOUT_THRESHOLD = 20.0       # % items out of stock
BED_VOL_THRESHOLD = 0.30        # std-dev of occupancy
DOC_ATT_THRESHOLD = 80.0        # % present
FOOTFALL_RATIO_THRESHOLD = 0.50 # vs district median
TEST_GAP_THRESHOLD = 30.0       # % missing required tests
STOCKOUT_DAYS_WARNING = 7       # days remaining → warning
STOCKOUT_DAYS_CRITICAL = 3      # days remaining → critical


# ── Internal helpers ──────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _calculate_facility_test_gap(facility: Facility, available_tests: set[str]) -> float:
    tier_name = facility.tier.value if hasattr(facility.tier, "value") else str(facility.tier)
    required = settings.required_tests_by_tier.get(tier_name, [])
    if not required:
        return 0.0
    missing = [t for t in required if t not in available_tests]
    return (len(missing) / len(required)) * 100.0


async def _existing_unacked_categories(
    db: AsyncSession, facility_id: uuid.UUID
) -> set[AlertCategory]:
    """Return the set of alert categories that already have an unacknowledged alert."""
    result = await db.execute(
        select(FacilityAlert.category).where(
            FacilityAlert.facility_id == facility_id,
            FacilityAlert.acknowledged_at == None,  # noqa: E711
        )
    )
    return {row[0] for row in result.all()}


async def _upsert_alert(
    db: AsyncSession,
    facility: Facility,
    severity: AlertSeverity,
    category: AlertCategory,
    message: str,
    detail: dict[str, Any] | None,
    existing_cats: set[AlertCategory],
) -> FacilityAlert | None:
    """Insert a new alert only if no unacknowledged alert for that category exists."""
    if category in existing_cats:
        return None

    alert = FacilityAlert(
        id=uuid.uuid4(),
        facility_id=facility.id,
        facility_name=facility.name,
        severity=severity,
        category=category,
        message=message,
        detail=json.dumps(detail) if detail else None,
    )
    db.add(alert)
    return alert


# ── Main evaluation logic ──────────────────────────────────────────────────────

async def _evaluate_all_facilities() -> None:
    """Full district-wide risk scan. Called by the scheduler every 6 hours."""
    log.info("[AI Scheduler] Starting district-wide facility risk scan…")
    try:
        async with AsyncSessionLocal() as db:
            await _run_scan(db)
        log.info("[AI Scheduler] District scan complete.")
    except Exception:
        log.exception("[AI Scheduler] Scan failed with unhandled exception")


async def _run_scan(db: AsyncSession) -> None:
    redis = get_redis()

    fac_result = await db.execute(select(Facility))
    facilities = list(fac_result.scalars().all())
    if not facilities:
        log.info("[AI Scheduler] No facilities found — skipping.")
        return

    # ── Compute district-wide footfall median ──────────────────────────────────
    facility_medians: dict[uuid.UUID, float] = {}
    for facility in facilities:
        ff_result = await db.execute(
            select(FootfallLog).where(
                FootfallLog.facility_id == facility.id,
                FootfallLog.department == None,  # noqa: E711
            )
        )
        logs = ff_result.scalars().all()
        if logs:
            facility_medians[facility.id] = float(np.median([l.patient_count for l in logs]))
        else:
            facility_medians[facility.id] = 0.0

    valid_medians = [m for m in facility_medians.values() if m > 0]
    overall_median = float(np.median(valid_medians)) if valid_medians else 0.0

    # ── Fetch item catalogue ───────────────────────────────────────────────────
    item_result = await db.execute(select(InventoryItem))
    items_by_id = {item.id: item for item in item_result.scalars().all()}

    new_alert_count = 0

    for facility in facilities:
        existing_cats = await _existing_unacked_categories(db, facility.id)
        new_alerts: list[FacilityAlert] = []

        # ── 1. Stock-out frequency ─────────────────────────────────────────────
        stock_result = await db.execute(
            select(StockLevel).where(StockLevel.facility_id == facility.id)
        )
        levels = list(stock_result.scalars().all())
        if levels:
            stockout_count = sum(1 for l in levels if float(l.quantity) <= 0)
            stockout_freq = (stockout_count / len(levels)) * 100.0
        else:
            stockout_freq = 0.0

        if stockout_freq > STOCKOUT_THRESHOLD:
            alert = await _upsert_alert(
                db, facility,
                AlertSeverity.critical,
                AlertCategory.stockout,
                f"{facility.name} has {stockout_freq:.1f}% of inventory items at zero stock.",
                {"stockout_frequency": stockout_freq, "stockout_count": stockout_count, "total_items": len(levels)},
                existing_cats,
            )
            if alert:
                new_alerts.append(alert)

        # ── 2. Bed volatility ──────────────────────────────────────────────────
        bed_result = await db.execute(
            select(Bed).where(Bed.facility_id == facility.id).order_by(Bed.updated_at.asc())
        )
        bed_records = list(bed_result.scalars().all())
        if len(bed_records) >= 2:
            rates = [
                r.occupied_beds / r.total_beds if r.total_beds > 0 else 0.0
                for r in bed_records
            ]
            bed_vol = float(np.std(rates))
        else:
            bed_vol = 0.0

        if bed_vol > BED_VOL_THRESHOLD:
            alert = await _upsert_alert(
                db, facility,
                AlertSeverity.warning,
                AlertCategory.bed_volatility,
                f"{facility.name} has highly volatile bed occupancy (σ = {bed_vol:.3f}). Check for unreported admissions/discharges.",
                {"bed_volatility": bed_vol},
                existing_cats,
            )
            if alert:
                new_alerts.append(alert)

        # ── 3. Doctor attendance ───────────────────────────────────────────────
        doc_result = await db.execute(
            select(Staff).where(
                Staff.facility_id == facility.id,
                Staff.role.ilike("%doctor%") | Staff.role.ilike("%medical officer%"),
            )
        )
        doctors = list(doc_result.scalars().all())
        if doctors:
            doc_ids = [d.id for d in doctors]
            att_result = await db.execute(
                select(AttendanceLog).where(AttendanceLog.staff_id.in_(doc_ids))
            )
            att_logs = list(att_result.scalars().all())
            if att_logs:
                present = sum(1 for l in att_logs if l.present)
                doc_att = (present / len(att_logs)) * 100.0
            else:
                doc_att = 100.0
        else:
            doc_att = 100.0

        if doc_att < DOC_ATT_THRESHOLD:
            alert = await _upsert_alert(
                db, facility,
                AlertSeverity.critical,
                AlertCategory.doctor_attendance,
                f"{facility.name} doctor attendance is {doc_att:.1f}% — below the 80% threshold.",
                {"doctor_attendance_pct": doc_att},
                existing_cats,
            )
            if alert:
                new_alerts.append(alert)

        # ── 4. Footfall vs district median ─────────────────────────────────────
        fac_median = facility_medians.get(facility.id, 0.0)
        footfall_ratio = fac_median / overall_median if overall_median > 0 else 1.0

        if footfall_ratio < FOOTFALL_RATIO_THRESHOLD:
            alert = await _upsert_alert(
                db, facility,
                AlertSeverity.warning,
                AlertCategory.footfall,
                f"{facility.name} is seeing only {footfall_ratio:.2f}× the district median footfall. It may be under-utilised or facing access barriers.",
                {"footfall_ratio": footfall_ratio, "facility_median": fac_median, "district_median": overall_median},
                existing_cats,
            )
            if alert:
                new_alerts.append(alert)

        # ── 5. Diagnostic test gap ─────────────────────────────────────────────
        test_result = await db.execute(
            select(TestAvailability).where(
                TestAvailability.facility_id == facility.id,
                TestAvailability.available == True,  # noqa: E712
            )
        )
        avail_rows = test_result.scalars().all()
        avail_set = {row.test_name for row in avail_rows}
        test_gap = _calculate_facility_test_gap(facility, avail_set)

        if test_gap > TEST_GAP_THRESHOLD:
            tier = facility.tier.value if hasattr(facility.tier, "value") else str(facility.tier)
            required = settings.required_tests_by_tier.get(tier, [])
            missing = [t for t in required if t not in avail_set]
            alert = await _upsert_alert(
                db, facility,
                AlertSeverity.warning,
                AlertCategory.diagnostic_gap,
                f"{facility.name} is missing {test_gap:.1f}% of required IPHS diagnostic tests.",
                {"test_gap_pct": test_gap, "missing_tests": missing},
                existing_cats,
            )
            if alert:
                new_alerts.append(alert)

        # ── 6. Demand forecasts → per-item stock-out alerts ────────────────────
        for sl in levels:
            item = items_by_id.get(sl.item_id)
            if not item:
                continue

            tx_result = await db.execute(
                select(StockTransaction).where(
                    StockTransaction.facility_id == facility.id,
                    StockTransaction.item_id == sl.item_id,
                    StockTransaction.delta < 0,
                ).order_by(StockTransaction.timestamp.desc()).limit(20)
            )
            txs = list(tx_result.scalars().all())
            if txs:
                total_dispensed = abs(sum(tx.delta for tx in txs))
                newest = txs[0].timestamp
                oldest = txs[-1].timestamp
                days_span = max((newest - oldest).days, 1)
                daily_rate = max(total_dispensed / days_span, 1.0)
            else:
                daily_rate = 5.0

            qty = float(sl.quantity)
            days_remaining = qty / daily_rate

            if days_remaining <= STOCKOUT_DAYS_CRITICAL and qty <= float(sl.reorder_threshold):
                severity = AlertSeverity.critical
                msg = (
                    f"{facility.name}: {item.name} will run out in ≈{days_remaining:.1f} days "
                    f"(current: {qty} {item.unit}, rate: {daily_rate:.1f}/day). CRITICAL."
                )
            elif days_remaining <= STOCKOUT_DAYS_WARNING and qty <= float(sl.reorder_threshold):
                severity = AlertSeverity.warning
                msg = (
                    f"{facility.name}: {item.name} will run out in ≈{days_remaining:.1f} days "
                    f"(current: {qty} {item.unit}, rate: {daily_rate:.1f}/day)."
                )
            else:
                continue  # stock is healthy

            # Use a composite detail key to allow per-item alerting
            # We bypass category dedup for individual items via direct insert
            stock_alert_cat = AlertCategory.stockout
            if stock_alert_cat not in existing_cats:
                alert = FacilityAlert(
                    id=uuid.uuid4(),
                    facility_id=facility.id,
                    facility_name=facility.name,
                    severity=severity,
                    category=stock_alert_cat,
                    message=msg,
                    detail=json.dumps({
                        "item_id": str(sl.item_id),
                        "item_name": item.name,
                        "quantity": qty,
                        "daily_rate": daily_rate,
                        "days_remaining": round(days_remaining, 1),
                        "reorder_threshold": float(sl.reorder_threshold),
                    }),
                )
                db.add(alert)
                new_alerts.append(alert)
                existing_cats.add(stock_alert_cat)  # one per facility per run

        # ── Flush new alerts and publish ───────────────────────────────────────
        if new_alerts:
            await db.flush()
            for alert in new_alerts:
                await db.refresh(alert)
                payload = {
                    "id": str(alert.id),
                    "facility_id": str(alert.facility_id),
                    "facility_name": alert.facility_name,
                    "severity": alert.severity.value,
                    "category": alert.category.value,
                    "message": alert.message,
                    "detail": alert.detail,
                    "created_at": alert.created_at.isoformat() if alert.created_at else None,
                }
                await publish(redis, str(facility.id), "alert.created", payload)
                # Also publish to the district-wide channel so the notification
                # bell updates without being subscribed to every facility
                await publish(redis, "district", "alert.created", payload)
            new_alert_count += len(new_alerts)

    await db.commit()
    log.info("[AI Scheduler] Inserted %d new alerts across %d facilities.", new_alert_count, len(facilities))


# ── Targeted single-facility stock check (called from stock router) ───────────

async def check_facility_stockouts(facility_id: uuid.UUID) -> None:
    """Run a fast stock-out scan for a single facility.

    Called after every stock level write so alerts appear immediately,
    not just on the next scheduled scan.
    """
    try:
        async with AsyncSessionLocal() as db:
            fac = await db.get(Facility, facility_id)
            if fac is None:
                return

            existing_cats = await _existing_unacked_categories(db, facility_id)

            stock_result = await db.execute(
                select(StockLevel).where(StockLevel.facility_id == facility_id)
            )
            levels = list(stock_result.scalars().all())
            if not levels:
                return

            stockout_count = sum(1 for l in levels if float(l.quantity) <= 0)
            stockout_freq = (stockout_count / len(levels)) * 100.0

            redis = get_redis()

            if stockout_freq > STOCKOUT_THRESHOLD:
                alert = await _upsert_alert(
                    db, fac,
                    AlertSeverity.critical,
                    AlertCategory.stockout,
                    f"{fac.name} has {stockout_freq:.1f}% of inventory items at zero stock.",
                    {"stockout_frequency": stockout_freq},
                    existing_cats,
                )
                if alert:
                    await db.flush()
                    await db.refresh(alert)
                    await db.commit()
                    payload = {
                        "id": str(alert.id),
                        "facility_id": str(alert.facility_id),
                        "facility_name": alert.facility_name,
                        "severity": alert.severity.value,
                        "category": alert.category.value,
                        "message": alert.message,
                        "detail": alert.detail,
                        "created_at": alert.created_at.isoformat() if alert.created_at else None,
                    }
                    await publish(redis, str(facility_id), "alert.created", payload)
                    await publish(redis, "district", "alert.created", payload)
                    return
            await db.commit()
    except Exception:
        log.exception("[AI Scheduler] check_facility_stockouts failed for %s", facility_id)


# ── Scheduler lifecycle ───────────────────────────────────────────────────────

def start_scheduler() -> AsyncIOScheduler:
    """Create and start the APScheduler. Call from FastAPI lifespan startup."""
    global _scheduler
    _scheduler = AsyncIOScheduler(timezone="UTC")
    _scheduler.add_job(
        _evaluate_all_facilities,
        trigger=IntervalTrigger(hours=6),
        id="district_ai_scan",
        name="District-wide AI Risk Scan",
        replace_existing=True,
        # Run immediately on startup so admins see data right away
        next_run_time=datetime.now(tz=timezone.utc),
    )
    _scheduler.start()
    log.info("[AI Scheduler] Started — district scan every 6 hours, immediate first run.")
    return _scheduler


def stop_scheduler() -> None:
    """Gracefully shut down the scheduler. Call from FastAPI lifespan shutdown."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        log.info("[AI Scheduler] Stopped.")
    _scheduler = None
