"""Pydantic v2 schemas for FootfallLog."""
from __future__ import annotations

import uuid
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class FootfallBase(BaseModel):
    date: date
    patient_count: int = Field(..., ge=0)
    department: Optional[str] = None  # NULL = whole-facility count
    is_simulated: bool = False
    basis: str


class FootfallCreate(FootfallBase):
    pass


class FootfallUpdate(BaseModel):
    patient_count: Optional[int] = Field(None, ge=0)
    department: Optional[str] = None
    is_simulated: Optional[bool] = None
    basis: Optional[str] = None


class FootfallRead(FootfallBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    facility_id: uuid.UUID
