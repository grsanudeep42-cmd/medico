"""ORM model for patient footfall logs at a facility."""
import uuid
from datetime import date
from typing import Optional

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDPrimaryKey


class FootfallLog(UUIDPrimaryKey, Base):
    """Daily patient footfall (OPD / IPD headcount) at a facility.

    Self-documenting provenance columns:
    - ``is_simulated`` — True if the count was model-generated.
    - ``basis``        — Source description (e.g. "HMIS weekly upload 2024-W22",
                         "Poisson simulation based on 2023 average").
    """

    __tablename__ = "footfall_logs"

    facility_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    patient_count: Mapped[int] = mapped_column(Integer, nullable=False)
    # NULL means whole-facility count, otherwise scoped to a department
    department: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Provenance
    is_simulated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    basis: Mapped[str] = mapped_column(Text, nullable=False)

    # ── Relationships ──────────────────────────────────────────────────────────
    facility: Mapped["Facility"] = relationship(  # noqa: F821
        "Facility", back_populates="footfall_logs"
    )
