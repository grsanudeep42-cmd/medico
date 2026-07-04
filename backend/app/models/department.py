"""ORM model for departments within a facility."""
import uuid

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKey


class Department(UUIDPrimaryKey, TimestampMixin, Base):
    """A clinical or administrative department inside a facility."""

    __tablename__ = "departments"

    facility_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)

    # ── Relationships ──────────────────────────────────────────────────────────
    facility: Mapped["Facility"] = relationship(  # noqa: F821
        "Facility", back_populates="departments"
    )
