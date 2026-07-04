"""Pydantic v2 schemas for Staff and AttendanceLog."""
from __future__ import annotations

import uuid
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ── Staff ──────────────────────────────────────────────────────────────────────

class StaffBase(BaseModel):
    role: str
    sanctioned: bool = True
    name: str


class StaffCreate(StaffBase):
    pass


class StaffUpdate(BaseModel):
    role: Optional[str] = None
    sanctioned: Optional[bool] = None
    name: Optional[str] = None


class StaffRead(StaffBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    facility_id: uuid.UUID


# ── AttendanceLog ──────────────────────────────────────────────────────────────

class AttendanceBase(BaseModel):
    staff_id: uuid.UUID
    date: date
    present: bool
    is_simulated: bool = False
    basis: str


class AttendanceCreate(AttendanceBase):
    pass


class AttendanceUpdate(BaseModel):
    present: Optional[bool] = None
    is_simulated: Optional[bool] = None
    basis: Optional[str] = None


class AttendanceRead(AttendanceBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
