"""Pydantic v2 schemas for Facility."""
from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.facility import FacilityTier, FacilityType


class FacilityBase(BaseModel):
    facility_id: str = Field(..., description="Human-readable external ID, e.g. 'MH-PHC-0042'")
    name: str
    facility_type: FacilityType
    tier: FacilityTier
    referral_parent_id: Optional[uuid.UUID] = None
    address: str
    lat: float
    lng: float
    sanctioned_beds: int = 0
    functional_beds_estimate: int = 0


class FacilityCreate(FacilityBase):
    pass


class FacilityUpdate(BaseModel):
    """All fields optional for PATCH-style updates."""
    name: Optional[str] = None
    facility_type: Optional[FacilityType] = None
    tier: Optional[FacilityTier] = None
    referral_parent_id: Optional[uuid.UUID] = None
    address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    sanctioned_beds: Optional[int] = None
    functional_beds_estimate: Optional[int] = None


class FacilityRead(FacilityBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
