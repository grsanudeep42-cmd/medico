"""CRUD router for Equipment resources, nested under a Facility."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.equipment import Equipment
from app.models.facility import Facility
from app.redis_client import get_redis
from app.schemas.equipment import EquipmentCreate, EquipmentRead, EquipmentUpdate
from app.services.publisher import publish

router = APIRouter(prefix="/facilities/{facility_id}/equipment", tags=["equipment"])


async def _require_facility(facility_id: uuid.UUID, db: AsyncSession) -> Facility:
    obj = await db.get(Facility, facility_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility not found")
    return obj


async def _get_eq_or_404(eq_id: uuid.UUID, facility_id: uuid.UUID, db: AsyncSession) -> Equipment:
    result = await db.execute(
        select(Equipment).where(Equipment.id == eq_id, Equipment.facility_id == facility_id)
    )
    obj = result.scalar_one_or_none()
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")
    return obj


@router.get("", response_model=list[EquipmentRead])
async def list_equipment(
    facility_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> list[Equipment]:
    await _require_facility(facility_id, db)
    result = await db.execute(
        select(Equipment).where(Equipment.facility_id == facility_id).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


@router.post("", response_model=EquipmentRead, status_code=status.HTTP_201_CREATED)
async def create_equipment(
    facility_id: uuid.UUID,
    body: EquipmentCreate,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> Equipment:
    await _require_facility(facility_id, db)
    eq = Equipment(facility_id=facility_id, **body.model_dump())
    db.add(eq)
    await db.commit()
    await db.refresh(eq)
    await publish(redis, str(facility_id), "equipment.created", EquipmentRead.model_validate(eq).model_dump())
    return eq


@router.get("/{eq_id}", response_model=EquipmentRead)
async def get_equipment(
    facility_id: uuid.UUID,
    eq_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Equipment:
    return await _get_eq_or_404(eq_id, facility_id, db)


@router.put("/{eq_id}", response_model=EquipmentRead)
async def update_equipment(
    facility_id: uuid.UUID,
    eq_id: uuid.UUID,
    body: EquipmentUpdate,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> Equipment:
    eq = await _get_eq_or_404(eq_id, facility_id, db)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(eq, field, value)
    await db.commit()
    await db.refresh(eq)
    await publish(redis, str(facility_id), "equipment.updated", EquipmentRead.model_validate(eq).model_dump())
    return eq


@router.delete("/{eq_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_equipment(
    facility_id: uuid.UUID,
    eq_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> None:
    eq = await _get_eq_or_404(eq_id, facility_id, db)
    eid = str(eq.id)
    await db.delete(eq)
    await db.commit()
    await publish(redis, str(facility_id), "equipment.deleted", {"id": eid})
