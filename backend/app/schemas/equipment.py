"""Pydantic v2 schemas for Equipment."""
from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict


class EquipmentBase(BaseModel):
    name: str
    category: str


class EquipmentCreate(EquipmentBase):
    pass


class EquipmentUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None


class EquipmentRead(EquipmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    facility_id: uuid.UUID
