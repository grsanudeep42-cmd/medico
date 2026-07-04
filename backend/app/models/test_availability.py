"""ORM model for diagnostic test availability at a facility."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDPrimaryKey


class TestAvailability(UUIDPrimaryKey, Base):
    """Whether a specific diagnostic test is currently available at a facility."""

    __tablename__ = "test_availability"

    facility_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # e.g. "CBC", "Blood Sugar (Random)", "X-Ray Chest PA", "RTPCR"
    test_name: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    available: Mapped[bool] = mapped_column(Boolean, nullable=False)
    last_checked: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    facility: Mapped["Facility"] = relationship(  # noqa: F821
        "Facility", back_populates="test_availabilities"
    )
