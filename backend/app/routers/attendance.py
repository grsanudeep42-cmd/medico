"""CRUD routers for Staff and AttendanceLog, nested under a Facility.

Attendance logs carry ``is_simulated`` + ``basis`` provenance columns.
Staff are managed at /facilities/{fid}/staff and attendance at
/facilities/{fid}/attendance.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.facility import Facility
from app.models.staff import AttendanceLog, Staff
from app.redis_client import get_redis
from app.schemas.attendance import (
    AttendanceCreate,
    AttendanceRead,
    AttendanceUpdate,
    StaffCreate,
    StaffRead,
    StaffUpdate,
)
from app.services.publisher import publish

staff_router = APIRouter(prefix="/facilities/{facility_id}/staff", tags=["staff"])
attendance_router = APIRouter(prefix="/facilities/{facility_id}/attendance", tags=["attendance"])


# ── Shared helpers ─────────────────────────────────────────────────────────────

async def _require_facility(facility_id: uuid.UUID, db: AsyncSession) -> Facility:
    obj = await db.get(Facility, facility_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility not found")
    return obj


async def _get_staff_or_404(staff_id: uuid.UUID, facility_id: uuid.UUID, db: AsyncSession) -> Staff:
    result = await db.execute(
        select(Staff).where(Staff.id == staff_id, Staff.facility_id == facility_id)
    )
    obj = result.scalar_one_or_none()
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff member not found")
    return obj


async def _get_attendance_or_404(log_id: uuid.UUID, db: AsyncSession) -> AttendanceLog:
    obj = await db.get(AttendanceLog, log_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance log not found")
    return obj


# ── Staff endpoints ────────────────────────────────────────────────────────────

@staff_router.get("", response_model=list[StaffRead])
async def list_staff(
    facility_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> list[Staff]:
    await _require_facility(facility_id, db)
    result = await db.execute(
        select(Staff).where(Staff.facility_id == facility_id).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


@staff_router.post("", response_model=StaffRead, status_code=status.HTTP_201_CREATED)
async def create_staff(
    facility_id: uuid.UUID,
    body: StaffCreate,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> Staff:
    await _require_facility(facility_id, db)
    member = Staff(facility_id=facility_id, **body.model_dump())
    db.add(member)
    await db.commit()
    await db.refresh(member)
    await publish(redis, str(facility_id), "staff.created", StaffRead.model_validate(member).model_dump())
    return member


@staff_router.get("/{staff_id}", response_model=StaffRead)
async def get_staff(
    facility_id: uuid.UUID,
    staff_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Staff:
    return await _get_staff_or_404(staff_id, facility_id, db)


@staff_router.put("/{staff_id}", response_model=StaffRead)
async def update_staff(
    facility_id: uuid.UUID,
    staff_id: uuid.UUID,
    body: StaffUpdate,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> Staff:
    member = await _get_staff_or_404(staff_id, facility_id, db)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(member, field, value)
    await db.commit()
    await db.refresh(member)
    await publish(redis, str(facility_id), "staff.updated", StaffRead.model_validate(member).model_dump())
    return member


@staff_router.delete("/{staff_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_staff(
    facility_id: uuid.UUID,
    staff_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> None:
    member = await _get_staff_or_404(staff_id, facility_id, db)
    sid = str(member.id)
    await db.delete(member)
    await db.commit()
    await publish(redis, str(facility_id), "staff.deleted", {"id": sid})


# ── Attendance endpoints ───────────────────────────────────────────────────────

@attendance_router.get("", response_model=list[AttendanceRead])
async def list_attendance(
    facility_id: uuid.UUID,
    skip: int = 0,
    limit: int = 200,
    db: AsyncSession = Depends(get_db),
) -> list[AttendanceLog]:
    await _require_facility(facility_id, db)
    # Join through Staff to scope by facility
    result = await db.execute(
        select(AttendanceLog)
        .join(Staff, AttendanceLog.staff_id == Staff.id)
        .where(Staff.facility_id == facility_id)
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


@attendance_router.post("", response_model=AttendanceRead, status_code=status.HTTP_201_CREATED)
async def create_attendance(
    facility_id: uuid.UUID,
    body: AttendanceCreate,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> AttendanceLog:
    # Verify staff belongs to this facility
    await _get_staff_or_404(body.staff_id, facility_id, db)
    log = AttendanceLog(**body.model_dump())
    db.add(log)
    await db.commit()
    await db.refresh(log)
    await publish(redis, str(facility_id), "attendance.created", AttendanceRead.model_validate(log).model_dump())
    return log


@attendance_router.get("/{log_id}", response_model=AttendanceRead)
async def get_attendance(
    facility_id: uuid.UUID,
    log_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> AttendanceLog:
    log = await _get_attendance_or_404(log_id, db)
    # Verify it belongs to this facility via staff
    await _get_staff_or_404(log.staff_id, facility_id, db)
    return log


@attendance_router.put("/{log_id}", response_model=AttendanceRead)
async def update_attendance(
    facility_id: uuid.UUID,
    log_id: uuid.UUID,
    body: AttendanceUpdate,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> AttendanceLog:
    log = await _get_attendance_or_404(log_id, db)
    await _get_staff_or_404(log.staff_id, facility_id, db)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(log, field, value)
    await db.commit()
    await db.refresh(log)
    await publish(redis, str(facility_id), "attendance.updated", AttendanceRead.model_validate(log).model_dump())
    return log


@attendance_router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attendance(
    facility_id: uuid.UUID,
    log_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> None:
    log = await _get_attendance_or_404(log_id, db)
    await _get_staff_or_404(log.staff_id, facility_id, db)
    lid = str(log.id)
    await db.delete(log)
    await db.commit()
    await publish(redis, str(facility_id), "attendance.deleted", {"id": lid})
