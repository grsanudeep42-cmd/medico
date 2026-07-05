"""Router for facility alerts and stock transfer approval.

Endpoints:
  GET  /alerts                   — list all alerts (filterable by severity/ack)
  GET  /alerts/unread-count      — integer count of unacknowledged alerts
  POST /alerts/{alert_id}/acknowledge — mark an alert acknowledged
  POST /ai/transfers/approve     — execute a real stock transfer between facilities
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.alert import AlertCategory, AlertSeverity, FacilityAlert
from app.models.facility import Facility
from app.models.inventory import (
    InventoryItem,
    StockLevel,
    StockTransaction,
    TransactionType,
)
from app.redis_client import get_redis
from app.services.publisher import publish

router = APIRouter(tags=["alerts"])


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class AlertRead(BaseModel):
    id: str
    facility_id: str
    facility_name: str
    severity: str
    category: str
    message: str
    detail: Optional[str]
    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[str]
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}


class AcknowledgeBody(BaseModel):
    acknowledged_by: str = "district_admin"


class TransferApproveBody(BaseModel):
    """Body for approving a resource redistribution recommendation."""
    from_facility_id: str
    to_facility_id: str
    item_id: str
    quantity: float
    recommendation_reason: str = ""


class TransferResult(BaseModel):
    success: bool
    from_facility_name: str
    to_facility_name: str
    item_name: str
    quantity_transferred: float
    from_new_quantity: float
    to_new_quantity: float
    message: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _alert_to_dict(alert: FacilityAlert) -> Dict[str, Any]:
    return {
        "id": str(alert.id),
        "facility_id": str(alert.facility_id),
        "facility_name": alert.facility_name,
        "severity": alert.severity.value,
        "category": alert.category.value,
        "message": alert.message,
        "detail": alert.detail,
        "acknowledged_at": alert.acknowledged_at,
        "acknowledged_by": alert.acknowledged_by,
        "created_at": alert.created_at,
    }


# ── Alert endpoints ───────────────────────────────────────────────────────────

@router.get("/alerts", response_model=List[AlertRead])
async def list_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity: info, warning, critical"),
    unacknowledged_only: bool = Query(False, description="Return only unacknowledged alerts"),
    facility_id: Optional[str] = Query(None, description="Filter to a single facility UUID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Return alerts with optional filters, newest first."""
    stmt = select(FacilityAlert).order_by(FacilityAlert.created_at.desc())

    if severity:
        try:
            sev_enum = AlertSeverity(severity)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid severity '{severity}'. Choose from: info, warning, critical",
            )
        stmt = stmt.where(FacilityAlert.severity == sev_enum)

    if unacknowledged_only:
        stmt = stmt.where(FacilityAlert.acknowledged_at == None)  # noqa: E711

    if facility_id:
        try:
            fid = uuid.UUID(facility_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid facility_id UUID")
        stmt = stmt.where(FacilityAlert.facility_id == fid)

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return [_alert_to_dict(a) for a in result.scalars().all()]


@router.get("/alerts/unread-count")
async def get_unread_count(db: AsyncSession = Depends(get_db)) -> Dict[str, int]:
    """Return the count of unacknowledged alerts — used by the notification bell."""
    result = await db.execute(
        select(func.count()).select_from(FacilityAlert).where(
            FacilityAlert.acknowledged_at == None  # noqa: E711
        )
    )
    count = result.scalar_one()
    return {"count": count}


@router.post("/alerts/{alert_id}/acknowledge", response_model=AlertRead)
async def acknowledge_alert(
    alert_id: uuid.UUID,
    body: AcknowledgeBody,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> Dict[str, Any]:
    """Mark a specific alert as acknowledged by a district administrator."""
    alert = await db.get(FacilityAlert, alert_id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    if alert.acknowledged_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Alert is already acknowledged",
        )

    alert.acknowledged_at = _now()
    alert.acknowledged_by = body.acknowledged_by
    await db.commit()
    await db.refresh(alert)

    payload = _alert_to_dict(alert)
    await publish(redis, str(alert.facility_id), "alert.acknowledged", payload)
    await publish(redis, "district", "alert.acknowledged", payload)

    return payload


# ── Real stock transfer endpoint ──────────────────────────────────────────────

@router.post("/ai/transfers/approve", response_model=TransferResult)
async def approve_transfer(
    body: TransferApproveBody,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> TransferResult:
    """Execute a stock redistribution between two facilities.

    This is the real endpoint that backs the "Approve Transfer" button in the
    AI Ops dashboard. It:
      1. Validates both facilities and the inventory item exist
      2. Validates the source facility has enough stock
      3. Atomically decrements source stock, increments destination stock
      4. Creates two StockTransaction records (transfer_out + transfer_in)
      5. Publishes Redis events to both facilities' WebSocket channels
    """
    try:
        from_fid = uuid.UUID(body.from_facility_id)
        to_fid = uuid.UUID(body.to_facility_id)
        item_id = uuid.UUID(body.item_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="from_facility_id, to_facility_id, and item_id must be valid UUIDs",
        )

    if body.quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="quantity must be greater than 0",
        )

    # ── Validate facilities ────────────────────────────────────────────────────
    from_facility = await db.get(Facility, from_fid)
    if from_facility is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source facility not found")

    to_facility = await db.get(Facility, to_fid)
    if to_facility is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Destination facility not found")

    # ── Validate inventory item ────────────────────────────────────────────────
    item = await db.get(InventoryItem, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory item not found")

    # ── Fetch stock levels ─────────────────────────────────────────────────────
    from_level_result = await db.execute(
        select(StockLevel).where(
            StockLevel.facility_id == from_fid,
            StockLevel.item_id == item_id,
        )
    )
    from_level = from_level_result.scalar_one_or_none()
    if from_level is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source facility has no stock record for item '{item.name}'",
        )

    to_level_result = await db.execute(
        select(StockLevel).where(
            StockLevel.facility_id == to_fid,
            StockLevel.item_id == item_id,
        )
    )
    to_level = to_level_result.scalar_one_or_none()

    # ── Validate sufficient source stock ───────────────────────────────────────
    from_qty = float(from_level.quantity)
    if from_qty < body.quantity:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Source facility only has {from_qty} {item.unit} of '{item.name}', "
                f"but transfer requires {body.quantity}."
            ),
        )

    now = _now()
    basis = f"AI-recommended transfer: {body.recommendation_reason}" if body.recommendation_reason else "AI-recommended resource redistribution"

    # ── Perform atomic update ──────────────────────────────────────────────────
    from_level.quantity = from_qty - body.quantity
    from_level.last_updated = now

    if to_level is None:
        # Destination facility has no record yet — create one
        to_level = StockLevel(
            facility_id=to_fid,
            item_id=item_id,
            quantity=body.quantity,
            reorder_threshold=from_level.reorder_threshold,
            last_updated=now,
        )
        db.add(to_level)
        to_new_qty = body.quantity
    else:
        to_new_qty = float(to_level.quantity) + body.quantity
        to_level.quantity = to_new_qty
        to_level.last_updated = now

    # ── Create transaction records ─────────────────────────────────────────────
    tx_out = StockTransaction(
        facility_id=from_fid,
        item_id=item_id,
        delta=-body.quantity,
        transaction_type=TransactionType.transfer_out,
        timestamp=now,
        is_simulated=False,
        basis=basis,
    )
    tx_in = StockTransaction(
        facility_id=to_fid,
        item_id=item_id,
        delta=body.quantity,
        transaction_type=TransactionType.transfer_in,
        timestamp=now,
        is_simulated=False,
        basis=basis,
    )
    db.add(tx_out)
    db.add(tx_in)

    await db.commit()
    await db.refresh(from_level)
    if to_level.id:
        await db.refresh(to_level)

    from_new_qty = float(from_level.quantity)

    # ── Publish events to both facility channels ───────────────────────────────
    transfer_payload = {
        "from_facility_id": str(from_fid),
        "from_facility_name": from_facility.name,
        "to_facility_id": str(to_fid),
        "to_facility_name": to_facility.name,
        "item_id": str(item_id),
        "item_name": item.name,
        "quantity": body.quantity,
        "from_new_quantity": from_new_qty,
        "to_new_quantity": to_new_qty,
    }
    await publish(redis, str(from_fid), "stock.transfer_out", transfer_payload)
    await publish(redis, str(to_fid), "stock.transfer_in", transfer_payload)
    await publish(redis, "district", "stock.transfer_completed", transfer_payload)

    return TransferResult(
        success=True,
        from_facility_name=from_facility.name,
        to_facility_name=to_facility.name,
        item_name=item.name,
        quantity_transferred=body.quantity,
        from_new_quantity=from_new_qty,
        to_new_quantity=to_new_qty,
        message=(
            f"Successfully transferred {body.quantity} {item.unit} of '{item.name}' "
            f"from {from_facility.name} to {to_facility.name}."
        ),
    )
