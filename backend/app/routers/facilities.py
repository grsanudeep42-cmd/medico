"""CRUD router for Facility resources."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.facility import Facility
from app.redis_client import get_redis
from app.schemas.facility import FacilityCreate, FacilityRead, FacilityUpdate
from app.services.publisher import publish

router = APIRouter(prefix="/facilities", tags=["facilities"])


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _get_or_404(facility_id: uuid.UUID, db: AsyncSession) -> Facility:
    result = await db.get(Facility, facility_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility not found")
    return result


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("", response_model=list[FacilityRead], status_code=status.HTTP_200_OK)
async def list_facilities(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> list[Facility]:
    result = await db.execute(select(Facility).offset(skip).limit(limit))
    return list(result.scalars().all())


@router.post("", response_model=FacilityRead, status_code=status.HTTP_201_CREATED)
async def create_facility(
    body: FacilityCreate,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> Facility:
    facility = Facility(**body.model_dump())
    db.add(facility)
    await db.commit()
    await db.refresh(facility)
    await publish(redis, str(facility.id), "facility.created", FacilityRead.model_validate(facility).model_dump())
    return facility


@router.get("/{facility_id}", response_model=FacilityRead)
async def get_facility(
    facility_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Facility:
    return await _get_or_404(facility_id, db)


@router.put("/{facility_id}", response_model=FacilityRead)
async def update_facility(
    facility_id: uuid.UUID,
    body: FacilityUpdate,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> Facility:
    facility = await _get_or_404(facility_id, db)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(facility, field, value)
    await db.commit()
    await db.refresh(facility)
    await publish(redis, str(facility.id), "facility.updated", FacilityRead.model_validate(facility).model_dump())
    return facility


@router.delete("/{facility_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_facility(
    facility_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> None:
    facility = await _get_or_404(facility_id, db)
    fid = str(facility.id)
    await db.delete(facility)
    await db.commit()
    await publish(redis, fid, "facility.deleted", {"id": fid})
