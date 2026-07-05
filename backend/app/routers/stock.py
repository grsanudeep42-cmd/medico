"""CRUD router for StockLevel resources with automatic StockTransaction logging.

On every POST / PUT to stock-levels, a corresponding StockTransaction is
auto-created:
  - POST (new level): delta = quantity, transaction_type = "receipt"
  - PUT  (update):    delta = new_qty − old_qty, transaction_type = "adjustment"
  - DELETE:           delta = -old_qty, transaction_type = "adjustment"

Both the stock_level change and the transaction are committed atomically.

Stock transactions are read-only via GET endpoints (they are never edited
directly through this API).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.facility import Facility
from app.models.inventory import StockLevel, StockTransaction, TransactionType
from app.redis_client import get_redis
from app.schemas.stock import (
    StockLevelCreate,
    StockLevelRead,
    StockLevelUpdate,
    StockTransactionRead,
)
from app.services.publisher import publish
from app.services.ai_scheduler import check_facility_stockouts

router = APIRouter(prefix="/facilities/{facility_id}", tags=["stock"])


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _require_facility(facility_id: uuid.UUID, db: AsyncSession) -> Facility:
    obj = await db.get(Facility, facility_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility not found")
    return obj


async def _get_level_or_404(level_id: uuid.UUID, facility_id: uuid.UUID, db: AsyncSession) -> StockLevel:
    result = await db.execute(
        select(StockLevel).where(
            StockLevel.id == level_id,
            StockLevel.facility_id == facility_id,
        )
    )
    obj = result.scalar_one_or_none()
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock level not found")
    return obj


def _now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


def _log_transaction(
    facility_id: uuid.UUID,
    item_id: uuid.UUID,
    delta: float,
    tx_type: TransactionType,
    basis: str = "API write",
) -> StockTransaction:
    return StockTransaction(
        facility_id=facility_id,
        item_id=item_id,
        delta=delta,
        transaction_type=tx_type,
        timestamp=_now_utc(),
        is_simulated=False,
        basis=basis,
    )


# ── Stock Level endpoints ──────────────────────────────────────────────────────

@router.get("/stock-levels", response_model=list[StockLevelRead])
async def list_stock_levels(
    facility_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> list[StockLevel]:
    await _require_facility(facility_id, db)
    result = await db.execute(
        select(StockLevel).where(StockLevel.facility_id == facility_id).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


@router.post("/stock-levels", response_model=StockLevelRead, status_code=status.HTTP_201_CREATED)
async def create_stock_level(
    facility_id: uuid.UUID,
    body: StockLevelCreate,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> StockLevel:
    await _require_facility(facility_id, db)
    level = StockLevel(facility_id=facility_id, **body.model_dump())
    tx = _log_transaction(facility_id, body.item_id, float(body.quantity), TransactionType.receipt)
    db.add(level)
    db.add(tx)
    await db.commit()
    await db.refresh(level)
    payload = StockLevelRead.model_validate(level).model_dump()
    await publish(redis, str(facility_id), "stock_level.created", payload)
    # Trigger immediate stock-out check for this facility
    await check_facility_stockouts(facility_id)
    return level


@router.get("/stock-levels/{level_id}", response_model=StockLevelRead)
async def get_stock_level(
    facility_id: uuid.UUID,
    level_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> StockLevel:
    return await _get_level_or_404(level_id, facility_id, db)


@router.put("/stock-levels/{level_id}", response_model=StockLevelRead)
async def update_stock_level(
    facility_id: uuid.UUID,
    level_id: uuid.UUID,
    body: StockLevelUpdate,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> StockLevel:
    level = await _get_level_or_404(level_id, facility_id, db)
    old_qty = float(level.quantity)

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(level, field, value)

    new_qty = float(level.quantity)
    delta = new_qty - old_qty
    if delta != 0:
        tx = _log_transaction(facility_id, level.item_id, delta, TransactionType.adjustment)
        db.add(tx)

    await db.commit()
    await db.refresh(level)
    payload = StockLevelRead.model_validate(level).model_dump()
    await publish(redis, str(facility_id), "stock_level.updated", payload)
    # Trigger immediate stock-out check (catches drops below threshold in real-time)
    await check_facility_stockouts(facility_id)
    return level


@router.delete("/stock-levels/{level_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stock_level(
    facility_id: uuid.UUID,
    level_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> None:
    level = await _get_level_or_404(level_id, facility_id, db)
    lid = str(level.id)
    item_id = level.item_id
    qty = float(level.quantity)
    if qty != 0:
        tx = _log_transaction(facility_id, item_id, -qty, TransactionType.adjustment, basis="API delete")
        db.add(tx)
    await db.delete(level)
    await db.commit()
    await publish(redis, str(facility_id), "stock_level.deleted", {"id": lid})


# ── Stock Transaction endpoints (read-only) ───────────────────────────────────

@router.get("/stock-transactions", response_model=list[StockTransactionRead])
async def list_stock_transactions(
    facility_id: uuid.UUID,
    skip: int = 0,
    limit: int = 200,
    db: AsyncSession = Depends(get_db),
) -> list[StockTransaction]:
    await _require_facility(facility_id, db)
    result = await db.execute(
        select(StockTransaction)
        .where(StockTransaction.facility_id == facility_id)
        .order_by(StockTransaction.timestamp.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


@router.get("/stock-transactions/{tx_id}", response_model=StockTransactionRead)
async def get_stock_transaction(
    facility_id: uuid.UUID,
    tx_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> StockTransaction:
    result = await db.execute(
        select(StockTransaction).where(
            StockTransaction.id == tx_id,
            StockTransaction.facility_id == facility_id,
        )
    )
    obj = result.scalar_one_or_none()
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return obj
