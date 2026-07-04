"""CRUD router for Department resources, nested under a Facility."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.department import Department
from app.models.facility import Facility
from app.redis_client import get_redis
from app.schemas.department import DepartmentCreate, DepartmentRead, DepartmentUpdate
from app.services.publisher import publish

router = APIRouter(prefix="/facilities/{facility_id}/departments", tags=["departments"])


async def _require_facility(facility_id: uuid.UUID, db: AsyncSession) -> Facility:
    obj = await db.get(Facility, facility_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility not found")
    return obj


async def _get_dept_or_404(dept_id: uuid.UUID, facility_id: uuid.UUID, db: AsyncSession) -> Department:
    result = await db.execute(
        select(Department).where(Department.id == dept_id, Department.facility_id == facility_id)
    )
    obj = result.scalar_one_or_none()
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    return obj


@router.get("", response_model=list[DepartmentRead])
async def list_departments(
    facility_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> list[Department]:
    await _require_facility(facility_id, db)
    result = await db.execute(
        select(Department).where(Department.facility_id == facility_id).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


@router.post("", response_model=DepartmentRead, status_code=status.HTTP_201_CREATED)
async def create_department(
    facility_id: uuid.UUID,
    body: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> Department:
    await _require_facility(facility_id, db)
    dept = Department(facility_id=facility_id, **body.model_dump())
    db.add(dept)
    await db.commit()
    await db.refresh(dept)
    await publish(redis, str(facility_id), "department.created", DepartmentRead.model_validate(dept).model_dump())
    return dept


@router.get("/{dept_id}", response_model=DepartmentRead)
async def get_department(
    facility_id: uuid.UUID,
    dept_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Department:
    return await _get_dept_or_404(dept_id, facility_id, db)


@router.put("/{dept_id}", response_model=DepartmentRead)
async def update_department(
    facility_id: uuid.UUID,
    dept_id: uuid.UUID,
    body: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> Department:
    dept = await _get_dept_or_404(dept_id, facility_id, db)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(dept, field, value)
    await db.commit()
    await db.refresh(dept)
    await publish(redis, str(facility_id), "department.updated", DepartmentRead.model_validate(dept).model_dump())
    return dept


@router.delete("/{dept_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    facility_id: uuid.UUID,
    dept_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> None:
    dept = await _get_dept_or_404(dept_id, facility_id, db)
    did = str(dept.id)
    await db.delete(dept)
    await db.commit()
    await publish(redis, str(facility_id), "department.deleted", {"id": did})
