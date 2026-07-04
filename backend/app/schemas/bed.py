"""Pydantic v2 schemas for Bed occupancy snapshots."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BedBase(BaseModel):
    total_beds: int = Field(..., ge=0)
    occupied_beds: int = Field(..., ge=0)
    updated_at: datetime


class BedCreate(BedBase):
    pass


class BedUpdate(BaseModel):
    total_beds: Optional[int] = Field(None, ge=0)
    occupied_beds: Optional[int] = Field(None, ge=0)
    updated_at: Optional[datetime] = None


class BedRead(BedBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    facility_id: uuid.UUID
