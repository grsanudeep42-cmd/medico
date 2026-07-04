"""ORM model for bed occupancy snapshots at a facility."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDPrimaryKey


class Bed(UUIDPrimaryKey, Base):
    """Point-in-time snapshot of bed occupancy at a facility."""

    __tablename__ = "beds"

    facility_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    total_beds: Mapped[int] = mapped_column(nullable=False, default=0)
    occupied_beds: Mapped[int] = mapped_column(nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    facility: Mapped["Facility"] = relationship(  # noqa: F821
        "Facility", back_populates="beds"
    )
