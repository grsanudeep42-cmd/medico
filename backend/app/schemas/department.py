"""Pydantic v2 schemas for Department."""
from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict


class DepartmentBase(BaseModel):
    name: str


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None


class DepartmentRead(DepartmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    facility_id: uuid.UUID
