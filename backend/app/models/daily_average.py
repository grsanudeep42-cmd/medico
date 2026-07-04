"""ORM model for real, published daily operational averages.

IMPORTANT: Every row here must originate from a real published source.
- ``source_url`` is NOT NULL — a citation is mandatory.
- ``is_simulated`` is intentionally absent; there is no simulated path for this table.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDPrimaryKey


class DailyAverage(UUIDPrimaryKey, Base):
    """Published daily average for a single operational metric at a facility."""

    __tablename__ = "daily_averages"

    facility_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # e.g. "outpatient_visits", "bed_occupancy_rate", "avg_wait_minutes"
    metric_name: Mapped[str] = mapped_column(Text, nullable=False, index=True)

    avg_value: Mapped[float] = mapped_column(Numeric(precision=12, scale=4), nullable=False)
    min_value: Mapped[Optional[float]] = mapped_column(
        Numeric(precision=12, scale=4), nullable=True
    )
    max_value: Mapped[Optional[float]] = mapped_column(
        Numeric(precision=12, scale=4), nullable=True
    )

    # Mandatory citation — never null, never empty
    source_url: Mapped[str] = mapped_column(Text, nullable=False)

    # Date/time to which this average applies (publication or reporting date)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    facility: Mapped["Facility"] = relationship(  # noqa: F821
        "Facility", back_populates="daily_averages"
    )
