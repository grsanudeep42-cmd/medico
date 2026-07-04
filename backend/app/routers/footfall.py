"""CRUD router for FootfallLog resources, nested under a Facility."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.facility import Facility
from app.models.footfall import FootfallLog
from app.redis_client import get_redis
from app.schemas.footfall import FootfallCreate, FootfallRead, FootfallUpdate
from app.services.publisher import publish

router = APIRouter(prefix="/facilities/{facility_id}/footfall", tags=["footfall"])


async def _require_facility(facility_id: uuid.UUID, db: AsyncSession) -> Facility:
    obj = await db.get(Facility, facility_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility not found")
    return obj


async def _get_log_or_404(log_id: uuid.UUID, facility_id: uuid.UUID, db: AsyncSession) -> FootfallLog:
    result = await db.execute(
        select(FootfallLog).where(
            FootfallLog.id == log_id,
            FootfallLog.facility_id == facility_id,
        )
    )
    obj = result.scalar_one_or_none()
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Footfall log not found")
    return obj


@router.get("", response_model=list[FootfallRead])
async def list_footfall(
    facility_id: uuid.UUID,
    skip: int = 0,
    limit: int = 200,
    db: AsyncSession = Depends(get_db),
) -> list[FootfallLog]:
    await _require_facility(facility_id, db)
    result = await db.execute(
        select(FootfallLog)
        .where(FootfallLog.facility_id == facility_id)
        .order_by(FootfallLog.date.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


@router.post("", response_model=FootfallRead, status_code=status.HTTP_201_CREATED)
async def create_footfall(
    facility_id: uuid.UUID,
    body: FootfallCreate,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> FootfallLog:
    await _require_facility(facility_id, db)
    log = FootfallLog(facility_id=facility_id, **body.model_dump())
    db.add(log)
    await db.commit()
    await db.refresh(log)
    await publish(redis, str(facility_id), "footfall.created", FootfallRead.model_validate(log).model_dump())
    return log


@router.get("/{log_id}", response_model=FootfallRead)
async def get_footfall(
    facility_id: uuid.UUID,
    log_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> FootfallLog:
    return await _get_log_or_404(log_id, facility_id, db)


@router.put("/{log_id}", response_model=FootfallRead)
async def update_footfall(
    facility_id: uuid.UUID,
    log_id: uuid.UUID,
    body: FootfallUpdate,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> FootfallLog:
    log = await _get_log_or_404(log_id, facility_id, db)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(log, field, value)
    await db.commit()
    await db.refresh(log)
    await publish(redis, str(facility_id), "footfall.updated", FootfallRead.model_validate(log).model_dump())
    return log


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_footfall(
    facility_id: uuid.UUID,
    log_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> None:
    log = await _get_log_or_404(log_id, facility_id, db)
    lid = str(log.id)
    await db.delete(log)
    await db.commit()
    await publish(redis, str(facility_id), "footfall.deleted", {"id": lid})
