"""CRUD router for Bed occupancy snapshots, nested under a Facility."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.bed import Bed
from app.models.facility import Facility
from app.redis_client import get_redis
from app.schemas.bed import BedCreate, BedRead, BedUpdate
from app.services.publisher import publish

router = APIRouter(prefix="/facilities/{facility_id}/beds", tags=["beds"])


async def _require_facility(facility_id: uuid.UUID, db: AsyncSession) -> Facility:
    obj = await db.get(Facility, facility_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility not found")
    return obj


async def _get_bed_or_404(bed_id: uuid.UUID, facility_id: uuid.UUID, db: AsyncSession) -> Bed:
    result = await db.execute(
        select(Bed).where(Bed.id == bed_id, Bed.facility_id == facility_id)
    )
    obj = result.scalar_one_or_none()
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bed snapshot not found")
    return obj


@router.get("", response_model=list[BedRead])
async def list_beds(
    facility_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> list[Bed]:
    await _require_facility(facility_id, db)
    result = await db.execute(
        select(Bed).where(Bed.facility_id == facility_id).order_by(Bed.updated_at.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


@router.post("", response_model=BedRead, status_code=status.HTTP_201_CREATED)
async def create_bed(
    facility_id: uuid.UUID,
    body: BedCreate,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> Bed:
    await _require_facility(facility_id, db)
    bed = Bed(facility_id=facility_id, **body.model_dump())
    db.add(bed)
    await db.commit()
    await db.refresh(bed)
    await publish(redis, str(facility_id), "bed.created", BedRead.model_validate(bed).model_dump())
    return bed


@router.get("/{bed_id}", response_model=BedRead)
async def get_bed(
    facility_id: uuid.UUID,
    bed_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Bed:
    return await _get_bed_or_404(bed_id, facility_id, db)


@router.put("/{bed_id}", response_model=BedRead)
async def update_bed(
    facility_id: uuid.UUID,
    bed_id: uuid.UUID,
    body: BedUpdate,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> Bed:
    bed = await _get_bed_or_404(bed_id, facility_id, db)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(bed, field, value)
    await db.commit()
    await db.refresh(bed)
    await publish(redis, str(facility_id), "bed.updated", BedRead.model_validate(bed).model_dump())
    return bed


@router.delete("/{bed_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bed(
    facility_id: uuid.UUID,
    bed_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> None:
    bed = await _get_bed_or_404(bed_id, facility_id, db)
    bid = str(bed.id)
    await db.delete(bed)
    await db.commit()
    await publish(redis, str(facility_id), "bed.deleted", {"id": bid})
