"""ORM model for medical/diagnostic equipment at a facility."""
import uuid

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKey


class Equipment(UUIDPrimaryKey, TimestampMixin, Base):
    """A piece of equipment (or class of equipment) at a facility."""

    __tablename__ = "equipment"

    facility_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    # Broad category, e.g. "Diagnostic Imaging", "Laboratory", "Surgical"
    category: Mapped[str] = mapped_column(Text, nullable=False)

    # ── Relationships ──────────────────────────────────────────────────────────
    facility: Mapped["Facility"] = relationship(  # noqa: F821
        "Facility", back_populates="equipment"
    )
