"""Pydantic v2 schemas for inventory items, stock levels, and stock transactions."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.inventory import TransactionType


# ── InventoryItem ──────────────────────────────────────────────────────────────

class InventoryItemBase(BaseModel):
    name: str
    category: str
    unit: str


class InventoryItemCreate(InventoryItemBase):
    pass


class InventoryItemUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None


class InventoryItemRead(InventoryItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID


# ── StockLevel ─────────────────────────────────────────────────────────────────

class StockLevelBase(BaseModel):
    item_id: uuid.UUID
    quantity: float = Field(..., ge=0)
    reorder_threshold: float = Field(0, ge=0)
    last_updated: datetime


class StockLevelCreate(StockLevelBase):
    pass


class StockLevelUpdate(BaseModel):
    quantity: Optional[float] = Field(None, ge=0)
    reorder_threshold: Optional[float] = Field(None, ge=0)
    last_updated: Optional[datetime] = None


class StockLevelRead(StockLevelBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    facility_id: uuid.UUID


# ── StockTransaction ───────────────────────────────────────────────────────────

class StockTransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    facility_id: uuid.UUID
    item_id: uuid.UUID
    delta: float
    transaction_type: TransactionType
    timestamp: datetime
    is_simulated: bool
    basis: str
