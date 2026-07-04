"""ORM models for inventory items, stock levels, and stock transactions."""
import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKey


class TransactionType(str, enum.Enum):
    receipt = "receipt"        # stock received from supply chain
    dispensed = "dispensed"    # issued to patient / ward
    adjustment = "adjustment"  # physical count correction
    expired = "expired"        # removed due to expiry
    transfer_in = "transfer_in"
    transfer_out = "transfer_out"


class InventoryItem(UUIDPrimaryKey, TimestampMixin, Base):
    """A master catalogue entry for a consumable or drug."""

    __tablename__ = "inventory_items"

    name: Mapped[str] = mapped_column(Text, nullable=False)
    # e.g. "Essential Medicine", "Consumable", "Reagent", "PPE"
    category: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    # Unit of measure, e.g. "tablets", "vials", "boxes"
    unit: Mapped[str] = mapped_column(Text, nullable=False)

    # ── Relationships ──────────────────────────────────────────────────────────
    stock_levels: Mapped[list["StockLevel"]] = relationship(
        "StockLevel", back_populates="item", cascade="all, delete-orphan"
    )
    stock_transactions: Mapped[list["StockTransaction"]] = relationship(
        "StockTransaction", back_populates="item", cascade="all, delete-orphan"
    )


class StockLevel(UUIDPrimaryKey, Base):
    """Current on-hand stock of an item at a specific facility."""

    __tablename__ = "stock_levels"

    facility_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    quantity: Mapped[float] = mapped_column(Numeric(precision=12, scale=3), nullable=False, default=0)
    reorder_threshold: Mapped[float] = mapped_column(
        Numeric(precision=12, scale=3), nullable=False, default=0
    )
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    facility: Mapped["Facility"] = relationship(  # noqa: F821
        "Facility", back_populates="stock_levels"
    )
    item: Mapped["InventoryItem"] = relationship("InventoryItem", back_populates="stock_levels")


class StockTransaction(UUIDPrimaryKey, Base):
    """An individual change to stock at a facility.

    Self-documenting provenance columns:
    - ``is_simulated`` — True if the movement was model-generated.
    - ``basis``        — Source description (e.g. "DVDMS upload", "demand forecast v3").
    """

    __tablename__ = "stock_transactions"

    facility_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Positive = stock in, negative = stock out
    delta: Mapped[float] = mapped_column(Numeric(precision=12, scale=3), nullable=False)
    transaction_type: Mapped[TransactionType] = mapped_column(
        SAEnum(TransactionType, name="transaction_type_enum", create_type=True), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    # Provenance
    is_simulated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    basis: Mapped[str] = mapped_column(Text, nullable=False)

    # ── Relationships ──────────────────────────────────────────────────────────
    facility: Mapped["Facility"] = relationship(  # noqa: F821
        "Facility", back_populates="stock_transactions"
    )
    item: Mapped["InventoryItem"] = relationship(
        "InventoryItem", back_populates="stock_transactions"
    )
