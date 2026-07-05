"""ORM model for AI-generated facility operational alerts."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKey


class AlertSeverity(str, enum.Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


class AlertCategory(str, enum.Enum):
    stockout = "stockout"
    bed_volatility = "bed_volatility"
    doctor_attendance = "doctor_attendance"
    footfall = "footfall"
    diagnostic_gap = "diagnostic_gap"
    resource_redistribution = "resource_redistribution"


class FacilityAlert(UUIDPrimaryKey, TimestampMixin, Base):
    """An AI-generated operational alert for a facility.

    Created automatically by the scheduler every time a new risk condition
    is detected. Acknowledged by district administrators in the dashboard.
    """

    __tablename__ = "facility_alerts"

    facility_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    facility_name: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[AlertSeverity] = mapped_column(
        SAEnum(AlertSeverity, name="alert_severity_enum", create_type=False), nullable=False
    )
    category: Mapped[AlertCategory] = mapped_column(
        SAEnum(AlertCategory, name="alert_category_enum", create_type=False), nullable=False
    )
    # Human-readable message for the admin
    message: Mapped[str] = mapped_column(Text, nullable=False)
    # Optional JSON blob for structured data (item name, qty, etc.)
    detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Acknowledgement fields — NULL means unacknowledged
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    acknowledged_by: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Relationships ──────────────────────────────────────────────────────────
    facility: Mapped["Facility"] = relationship(  # noqa: F821
        "Facility", back_populates="alerts"
    )
